"""USB controller detection module"""

import re
from typing import Any

from src.parsers.iommu import get_iommu_group
from src.parsers.pci import parse_subsystem_id
from src.utils import run_command


class USBControllerDetector:
    """Detect USB controllers"""

    @staticmethod
    def detect() -> list[dict[str, Any]]:
        """Detect USB controllers"""
        usb_controllers = []

        # Get USB controllers from lspci
        lspci_all = run_command(["lspci", "-nn"])
        lspci_output = ""
        for line in lspci_all.split("\n"):
            if "usb controller" in line.lower():
                lspci_output += line + "\n"

        for line in lspci_output.split("\n"):
            if not line.strip():
                continue

            match = re.match(r"([0-9a-f:\.]+)\s+.*?:\s+(.+)\s+\[([0-9a-f]+):([0-9a-f]+)\]", line)
            if match:
                pci_addr, description, vendor_id, device_id = match.groups()

                controller = {
                    "name": description.strip(),
                    "pci_address": f"0000:{pci_addr}",
                    "pci_ids": {"vendor": vendor_id, "device": device_id, "full": f"{vendor_id}:{device_id}"},
                }

                # Determine USB version from description
                if "xHCI" in description or "USB 3" in description:
                    controller["usb_version"] = "3.x"
                elif "EHCI" in description or "USB 2" in description:
                    controller["usb_version"] = "2.0"
                elif "UHCI" in description or "OHCI" in description or "USB 1" in description:
                    controller["usb_version"] = "1.x"

                # Get IOMMU group
                full_pci_addr = f"0000:{pci_addr}"
                iommu_group = get_iommu_group(full_pci_addr)
                if iommu_group is not None:
                    controller["iommu_group"] = iommu_group

                # Get subsystem ID
                lspci_verbose = run_command(["lspci", "-vnn", "-s", pci_addr])
                subsystem_id = parse_subsystem_id(lspci_verbose)
                if subsystem_id:
                    controller["subsystem_id"] = subsystem_id

                usb_controllers.append(controller)

        return usb_controllers
