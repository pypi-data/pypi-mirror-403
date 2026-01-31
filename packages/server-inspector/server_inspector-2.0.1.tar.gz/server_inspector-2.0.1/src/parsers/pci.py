"""PCI device parsing utilities"""

import re
from dataclasses import dataclass


@dataclass
class PCIDevice:
    """Parsed PCI device information"""

    pci_address: str
    description: str
    vendor_id: str
    device_id: str

    @property
    def full_id(self) -> str:
        """Return full PCI ID in format vendor:device"""
        return f"{self.vendor_id}:{self.device_id}"


def parse_pci_device(lspci_line: str) -> PCIDevice | None:
    """Parse PCI device from lspci output

    Args:
        lspci_line: Single line from lspci -nn output

    Returns:
        PCIDevice object if parsing succeeds, None otherwise

    Example:
        >>> parse_pci_device("00:1f.6 Ethernet controller: Intel Corporation [8086:15d7]")
        PCIDevice(pci_address='00:1f.6', description='Ethernet controller: Intel Corporation',
                  vendor_id='8086', device_id='15d7')
    """
    # Match pattern: "PCI_ADDR DEVICE_TYPE: Description [VENDOR:DEVICE]"
    match = re.match(r"([0-9a-f:\.]+)\s+.*?:\s+(.+)\s+\[([0-9a-f]+):([0-9a-f]+)\]", lspci_line)

    if not match:
        return None

    pci_addr, description, vendor_id, device_id = match.groups()

    return PCIDevice(pci_address=pci_addr, description=description.strip(), vendor_id=vendor_id, device_id=device_id)


def parse_pci_ids(lspci_line: str) -> tuple[str, str] | None:
    """Extract PCI vendor and device IDs from lspci output

    Args:
        lspci_line: Single line from lspci -nn output

    Returns:
        Tuple of (vendor_id, device_id) if found, None otherwise

    Example:
        >>> parse_pci_ids("00:1f.6 Ethernet controller: Intel Corporation [8086:15d7]")
        ('8086', '15d7')
    """
    match = re.search(r"\[([0-9a-f]+):([0-9a-f]+)\]", lspci_line)
    if match:
        return match.group(1), match.group(2)
    return None


def parse_subsystem_id(lspci_verbose_output: str) -> str | None:
    """Extract subsystem ID from lspci -vnn output

    Args:
        lspci_verbose_output: Output from lspci -vnn for a specific device

    Returns:
        Subsystem ID in format "vendor:device" or None if not found

    Example:
        >>> parse_subsystem_id("Subsystem: ASUSTeK Computer Inc. [1043:8694]")
        '1043:8694'
    """
    for line in lspci_verbose_output.split("\n"):
        if "Subsystem:" in line:
            match = re.search(r"\[([0-9a-f]+):([0-9a-f]+)\]", line)
            if match:
                sub_vendor, sub_device = match.groups()
                return f"{sub_vendor}:{sub_device}"
    return None


def extract_pci_address_from_path(device_path: str) -> str | None:
    """Extract PCI address from sysfs device path

    Args:
        device_path: Path like "../../0000:15:00.0" or symlink target

    Returns:
        PCI address in format "0000:15:00.0" or None if not found

    Example:
        >>> extract_pci_address_from_path("../../0000:15:00.0")
        '0000:15:00.0'
    """
    match = re.search(r"([0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f])", device_path)
    if match:
        return match.group(1)
    return None
