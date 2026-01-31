"""System information detection module"""

import importlib.util
from pathlib import Path
from typing import Any

from src.utils import run_command

# Check if psutil is available
PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None

if PSUTIL_AVAILABLE:
    import psutil


class SystemDetector:
    """Detect system information"""

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect system information"""
        system_data: dict[str, Any] = {}

        # Boot mode
        system_data["boot_mode"] = "UEFI" if Path("/sys/firmware/efi").exists() else "Legacy BIOS"

        # Secure Boot status
        if Path("/sys/firmware/efi").exists():
            mokutil_output = run_command(["mokutil", "--sb-state"])
            secureboot = ""
            for line in mokutil_output.split("\n"):
                if "SecureBoot" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        secureboot = parts[1]
                    break
            if secureboot:
                system_data["secure_boot"] = secureboot
            else:
                # Alternative method - check SecureBoot EFI variable
                try:
                    efi_vars_path = Path("/sys/firmware/efi/efivars")
                    secureboot_files = list(efi_vars_path.glob("SecureBoot-*"))
                    if secureboot_files:
                        # Read the file (last byte indicates status)
                        with open(secureboot_files[0], "rb") as f:
                            data = f.read()
                            if data and len(data) > 0:
                                last_byte = data[-1]
                                if last_byte == 1:
                                    system_data["secure_boot"] = "enabled"
                                elif last_byte == 0:
                                    system_data["secure_boot"] = "disabled"
                except (OSError, PermissionError, IndexError):
                    pass

        # TPM detection
        try:
            tpm_devs = list(Path("/dev").glob("tpm*"))
            if tpm_devs:
                system_data["tpm_present"] = True
                # Try to get TPM version
                tpm_version_file = Path("/sys/class/tpm/tpm0/tpm_version_major")
                if tpm_version_file.exists():
                    try:
                        tpm_version = tpm_version_file.read_text().strip()
                        if tpm_version:
                            system_data["tpm_version"] = f"{tpm_version}.0"
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

        # OS info
        system_data["hostname"] = run_command(["hostname"])
        system_data["kernel"] = run_command(["uname", "-r"])

        # Parse /etc/os-release for OS name
        os_name = "Unknown"
        try:
            os_release = Path("/etc/os-release")
            if os_release.exists():
                os_release_content = os_release.read_text()
                for line in os_release_content.split("\n"):
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=", 1)[1].strip('"')
                        break
        except (OSError, PermissionError):
            pass
        system_data["os"] = os_name

        # Uptime
        if PSUTIL_AVAILABLE:
            import datetime

            boot_time = psutil.boot_time()
            system_data["boot_time"] = datetime.datetime.fromtimestamp(boot_time).isoformat()

        return system_data
