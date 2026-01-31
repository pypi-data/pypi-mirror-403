"""Storage detection module"""

import os
import re
from pathlib import Path
from typing import Any

from src.utils import TB_TO_GB_MULTIPLIER, run_command, sanitize_device_name


class StorageDetector:
    """Detect storage devices and recommend pool assignments"""

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect storage devices"""
        storage_data: dict[str, Any] = {"devices": []}

        # Get block devices
        lsblk_output = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE,ROTA,MODEL", "-n"])

        for line in lsblk_output.split("\n"):
            if not line.strip():
                continue

            parts = line.split(maxsplit=4)
            if len(parts) < 4:
                continue

            name, size, dev_type, rota = parts[:4]
            model = parts[4].strip() if len(parts) > 4 else "Unknown"

            if dev_type != "disk":
                continue

            # Sanitize device name to prevent shell injection
            name = sanitize_device_name(name)
            if not name:
                continue

            # Skip USB devices (they're removable media, not permanent storage)
            # Check if device is on USB bus or has 'usb' in the by-id path
            try:
                by_id_path = Path("/dev/disk/by-id")
                if by_id_path.exists():
                    for symlink in by_id_path.iterdir():
                        if symlink.is_symlink():
                            target = str(symlink.resolve())
                            if target.endswith(name) and "usb" in str(symlink).lower():
                                # Skip USB device
                                name = ""
                                break
            except (OSError, PermissionError):
                pass

            if not name:
                continue

            # Parse size to GB
            size_gb = 0
            if "T" in size:
                size_gb = int(float(size.replace("T", "")) * TB_TO_GB_MULTIPLIER)
            elif "G" in size:
                size_gb = int(float(size.replace("G", "")))

            # Determine type
            disk_type = "HDD" if rota == "1" else "SSD"
            if "nvme" in name:
                disk_type = "NVMe"

            # Extract hardware identifiers (WWN, EUI, serial)
            # These are stable across boots and don't depend on enumeration order
            wwn = None
            eui = None
            by_id_links = []

            try:
                by_id_path = Path("/dev/disk/by-id")
                if by_id_path.exists():
                    # Collect all matching symlinks
                    for symlink in by_id_path.iterdir():
                        if symlink.is_symlink() and "-part" not in str(symlink):
                            try:
                                target = str(symlink.resolve())
                                if target.endswith(name):
                                    link_name = symlink.name
                                    by_id_links.append(link_name)

                                    # Extract WWN (World Wide Name)
                                    if link_name.startswith("wwn-"):
                                        wwn = link_name.replace("wwn-", "")

                                    # Extract EUI (Extended Unique Identifier) for NVMe
                                    if link_name.startswith("nvme-eui."):
                                        eui = link_name.replace("nvme-", "").split("_")[0]  # Remove namespace suffix
                            except (OSError, PermissionError):
                                pass
            except (OSError, PermissionError):
                pass

            # Get serial from lsblk
            serial = run_command(["lsblk", "-no", "SERIAL", f"/dev/{name}"])

            # Determine interface - only report what we can confirm
            interface = "Unknown"
            if "nvme" in name:
                # NVMe devices are PCIe-based
                nvme_info = run_command(["nvme", "id-ctrl", f"/dev/{name}"])
                if nvme_info:
                    interface = "PCIe NVMe"
                else:
                    # NVMe device but can't query details
                    interface = "NVMe"
            else:
                # For non-NVMe, check if we can determine the bus type
                # Most common are SATA or SAS, but without querying the actual
                # link speed negotiated, we can't assume 6Gb/s vs 3Gb/s
                # Report generic "SATA" if it appears to be SATA-connected
                sys_block_path = Path(f"/sys/block/{name}")
                if sys_block_path.exists():
                    # Check if it's ATA (which means SATA)
                    device_link_path = sys_block_path / "device"
                    if device_link_path.exists():
                        try:
                            device_real_path = str(device_link_path.resolve())
                            if "ata" in device_real_path:
                                interface = "SATA"
                        except (OSError, RuntimeError):
                            pass
                    # Otherwise leave as Unknown (could be SAS, USB, etc.)

            # Get physical sector size (for ashift calculation)
            physical_block_size = 512  # Default fallback
            try:
                size_path = Path(f"/sys/block/{name}/queue/physical_block_size")
                if size_path.exists():
                    physical_block_size = int(size_path.read_text().strip())
            except (OSError, ValueError):
                pass

            # Build device info with hardware identifiers as source of truth
            device = {
                "name": name,  # Kernel name (unstable, for reference only)
                "model": model,
                "model_id": model.replace(" ", "_"),
                "capacity_gb": size_gb,
                "type": disk_type,
                "interface": interface,
                "serial": serial if serial else f"SERIAL_PLACEHOLDER_{name}",
                "wwn": wwn,  # World Wide Name (if available)
                "eui": eui,  # Extended Unique Identifier (if available)
                "physical_block_size": physical_block_size,
                "by_id_links": by_id_links,  # All symlinks for debugging
            }

            # Get SMART data if smartctl is available and running as root
            if os.geteuid() == 0:
                smart_data: dict[str, Any] = {}

                # Get SMART health status
                smart_health = run_command(["smartctl", "-H", f"/dev/{name}"])
                if smart_health:
                    if "PASSED" in smart_health or "OK" in smart_health:
                        smart_data["health_status"] = "PASSED"
                    elif "FAILED" in smart_health:
                        smart_data["health_status"] = "FAILED"

                # Get specific SMART attributes
                smart_all = run_command(["smartctl", "-A", f"/dev/{name}"])
                if smart_all:
                    # Temperature
                    temp_match = re.search(r"Temperature.*\s+(\d+)(?:\s+\(|$)", smart_all)
                    if temp_match:
                        smart_data["temperature_celsius"] = int(temp_match.group(1))

                    # Power-on hours
                    hours_match = re.search(r"Power_On_Hours.*\s+(\d+)$", smart_all, re.MULTILINE)
                    if hours_match:
                        smart_data["power_on_hours"] = int(hours_match.group(1))

                    # For SSDs: wear level / percentage used
                    wear_match = re.search(r"Wear_Leveling_Count.*\s+(\d+)$", smart_all, re.MULTILINE)
                    if wear_match:
                        smart_data["wear_leveling"] = int(wear_match.group(1))

                    percent_used = re.search(r"Percentage Used.*\s+(\d+)%", smart_all)
                    if percent_used:
                        smart_data["percentage_used"] = int(percent_used.group(1))

                # Get SMART info (model, serial, etc from SMART perspective)
                smart_info = run_command(["smartctl", "-i", f"/dev/{name}"])
                if smart_info:
                    # Firmware version
                    firmware_match = re.search(r"Firmware Version:\s+(.+)", smart_info)
                    if firmware_match:
                        smart_data["firmware_version"] = firmware_match.group(1).strip()

                if smart_data:
                    device["smart"] = smart_data

            storage_data["devices"].append(device)

        return storage_data
