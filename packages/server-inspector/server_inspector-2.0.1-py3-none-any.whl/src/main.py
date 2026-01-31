"""Main inspector proxmox-wizard."""

import contextlib
import importlib.util
import json
import os
import sys
from datetime import datetime
from typing import Any

from .colors import Colors
from .detectors.cpu import CPUDetector
from .detectors.gpu import GPUDetector
from .detectors.ipmi import IPMIDetector
from .detectors.memory import MemoryDetector
from .detectors.motherboard import MotherboardDetector
from .detectors.network import NetworkDetector
from .detectors.storage import StorageDetector
from .detectors.system import SystemDetector
from .detectors.usb import USBControllerDetector
from .utils import print_error, print_header, print_status, print_success, print_warning

# Version
VERSION = "2.0.0"

# Check dependencies
DEPS_AVAILABLE = {
    "psutil": importlib.util.find_spec("psutil") is not None,
    "cpuinfo": importlib.util.find_spec("cpuinfo") is not None,
    "pyudev": importlib.util.find_spec("pyudev") is not None,
    "netifaces": importlib.util.find_spec("netifaces") is not None,
}


class ServerInspector:
    """Main inspector proxmox-wizard."""

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.specs: dict[str, Any] = {
            "collection_info": {
                "timestamp": datetime.now().isoformat(),
                "inspector_version": VERSION,
                "method": "local",
                "server_name": server_name,
            },
            "server": {},
            "storage": {},
            "network": {},
            "gpu": [],
            "usb_controllers": [],
            "motherboard": {},
            "ipmi": {},
            "system": {},
        }

    def run(self) -> dict[str, Any]:
        """Run all detection modules"""
        print_header(f"HOME SERVER HARDWARE INSPECTOR - {self.server_name}")

        # Check if running as root
        if os.geteuid() != 0:
            print_warning("Not running as root - some details will be limited")
            print_warning("Run with: sudo python3 server_inspector.py")
            print()

        # Show available dependencies
        missing = [dep for dep, avail in DEPS_AVAILABLE.items() if not avail]
        if missing:
            print_warning(f"Missing optional dependencies: {', '.join(missing)}")
            print("   Some features may be limited.")
            print("   Run install-dependencies.sh to install dependencies")
            print()

        # Run detection
        print_status("🔍", "Detecting CPU...")
        self.specs["server"]["cpu"] = CPUDetector.detect()
        print_success(f"CPU: {self.specs['server']['cpu']['model']}")

        print_status("🔍", "Detecting Memory...")
        self.specs["server"]["memory"] = MemoryDetector.detect()
        print_success(f"Memory: {self.specs['server']['memory'].get('total_gb', '?')} GB")

        print_status("🔍", "Detecting Storage...")
        self.specs["storage"] = StorageDetector.detect()
        print_success(f"Storage: {len(self.specs['storage']['devices'])} device(s) found")

        print_status("🔍", "Detecting Network...")
        self.specs["network"] = NetworkDetector.detect()
        print_success(f"Network: {len(self.specs['network']['interfaces'])} interface(s) found")

        print_status("🔍", "Detecting GPU...")
        self.specs["gpu"] = GPUDetector.detect()
        if self.specs["gpu"]:
            print_success(f"GPU: {len(self.specs['gpu'])} device(s) found")
        else:
            print_status("ℹ️", "No discrete GPU detected")

        print_status("🔍", "Detecting USB Controllers...")
        self.specs["usb_controllers"] = USBControllerDetector.detect()
        print_success(f"USB: {len(self.specs['usb_controllers'])} controller(s) found")

        print_status("🔍", "Detecting Motherboard...")
        self.specs["motherboard"] = MotherboardDetector.detect()
        if self.specs["motherboard"].get("product_name"):
            print_success(f"Motherboard: {self.specs['motherboard']['product_name']}")
        else:
            print_status("ℹ️", "Motherboard info limited (not running as root)")

        print_status("🔍", "Detecting IPMI/BMC...")
        self.specs["ipmi"] = IPMIDetector.detect()
        if self.specs["ipmi"].get("device_present"):
            print_success(f"IPMI: Detected ({self.specs['ipmi'].get('manufacturer', 'Unknown')})")
        else:
            print_status("ℹ️", "No IPMI/BMC detected")

        print_status("🔍", "Detecting System Info...")
        self.specs["system"] = SystemDetector.detect()
        print_success(f"System: {self.specs['system']['boot_mode']}")

        return self.specs

    def save_json(self, output_file: str) -> None:
        """Save specs to JSON file"""
        import os
        import tempfile

        # Write to temp file first (atomic operation)
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(output_file) or ".", prefix=".tmp_specs_")
        try:
            with os.fdopen(temp_fd, "w") as f:
                json.dump(self.specs, f, indent=2)
            # Atomic rename
            os.replace(temp_path, output_file)
            # Sync to ensure data is flushed to disk (critical for USB)
            os.sync()
            print_success(f"Saved to: {output_file}")
        except Exception:
            # Clean up temp file on error
            with contextlib.suppress(OSError):
                os.unlink(temp_path)
            raise

    def print_summary(self) -> None:
        """Print summary of detected hardware"""
        print_header("DETECTION SUMMARY")

        cpu = self.specs["server"]["cpu"]
        mem = self.specs["server"]["memory"]

        print(f"  CPU: {cpu.get('model', 'Unknown')}")
        print(f"  Cores: {cpu.get('cores', '?')} physical / {cpu.get('threads', '?')} logical")
        print(f"  RAM: {mem.get('total_gb', '?')} GB", end="")
        if mem.get("type"):
            print(f" ({mem.get('type')} @ {mem.get('speed', 'Unknown')})")
        else:
            print()
        print(f"  Storage: {len(self.specs['storage']['devices'])} device(s)")
        print(f"  Network: {len(self.specs['network']['interfaces'])} interface(s)")
        print(f"  GPU: {len(self.specs['gpu'])} device(s)")
        print()

        # Proxmox readiness
        virt_supported = cpu.get("virtualization_supported", False)
        if virt_supported:
            print_success("Ready for Proxmox VE (virtualization supported)")
        else:
            print_error("Virtualization not supported - cannot run Proxmox VE")


def main() -> None:
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Server Hardware Inspector - Auto-detect hardware for home server deployment",
        epilog="Example: server-inspector white",
    )
    parser.add_argument("name", help="Server name (e.g., white, black, aio)")
    parser.add_argument("--output", "-o", help="Override output file path (default: server-specs-<name>.json)")

    args = parser.parse_args()

    # Default output filename based on server name
    output_file = args.output or f"server-specs-{args.name}.json"

    try:
        inspector = ServerInspector(args.name)
        inspector.run()
        inspector.save_json(output_file)
        inspector.print_summary()

        print()
        print(f"{Colors.BOLD}Next Steps:{Colors.END}")
        print(f"  1. Review {output_file} (optional)")
        print("  2. Unmount and shutdown:")
        print("     cd / && sync && umount /mnt/persistence")
        print("     poweroff")
        print("  3. Remove USB and insert into admin PC")
        print(f"  4. Import: proxmox-wizard hardware-detect {args.name} --usb-device /dev/sdX")
        print()

    except KeyboardInterrupt:
        # User pressed Ctrl+C to abort
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.END}")
        sys.exit(1)
    except FileNotFoundError as e:
        # Output file path doesn't exist or cannot be created
        print_error(f"File error: {e}")
        sys.exit(1)
    except PermissionError as e:
        # Cannot write to output file (permission denied)
        print_error(f"Permission denied: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        # Invalid JSON when saving specs
        print_error(f"JSON encoding error: {e}")
        sys.exit(1)
    except OSError as e:
        # Other OS-level errors (disk full, etc.)
        print_error(f"OS error: {e}")
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected errors (last resort handler)
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
