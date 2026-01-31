"""IOMMU group detection utilities"""

from pathlib import Path


def get_iommu_group(pci_address: str) -> int | None:
    """Get IOMMU group number for PCI device

    Args:
        pci_address: PCI address in format "0000:00:00.0"

    Returns:
        IOMMU group number or None if not found/not enabled

    Example:
        >>> get_iommu_group("0000:01:00.0")
        1
    """
    iommu_path = Path(f"/sys/bus/pci/devices/{pci_address}/iommu_group")

    if not iommu_path.exists() or not iommu_path.is_symlink():
        return None

    try:
        # Resolve symlink to get path like "/sys/kernel/iommu_groups/1"
        group_link = iommu_path.resolve()
        group_name = group_link.name

        if group_name.isdigit():
            return int(group_name)
    except (OSError, RuntimeError, ValueError):
        pass

    return None


def is_iommu_enabled() -> bool:
    """Check if IOMMU is enabled in the system

    Returns:
        True if IOMMU is enabled, False otherwise

    Note:
        Checks for presence of any IOMMU group in sysfs
    """
    iommu_groups_path = Path("/sys/kernel/iommu_groups")
    if not iommu_groups_path.exists():
        return False

    try:
        # Check if there are any IOMMU groups
        groups = list(iommu_groups_path.iterdir())
        return len(groups) > 0
    except (OSError, PermissionError):
        return False


def get_iommu_devices_in_group(group_number: int) -> list[str]:
    """Get all PCI devices in a specific IOMMU group

    Args:
        group_number: IOMMU group number

    Returns:
        List of PCI addresses in the group

    Example:
        >>> get_iommu_devices_in_group(1)
        ['0000:01:00.0', '0000:01:00.1']
    """
    group_path = Path(f"/sys/kernel/iommu_groups/{group_number}/devices")

    if not group_path.exists():
        return []

    devices = []
    try:
        for device_link in group_path.iterdir():
            if device_link.is_symlink():
                devices.append(device_link.name)
    except (OSError, PermissionError):
        pass

    return devices
