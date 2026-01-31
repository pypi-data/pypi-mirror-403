"""Network detection module"""

import contextlib
import importlib.util
import re
from pathlib import Path
from typing import Any

from src.parsers.iommu import get_iommu_group
from src.parsers.pci import extract_pci_address_from_path, parse_pci_ids, parse_subsystem_id
from src.utils import MBPS_TO_GBPS_DIVISOR, run_command, sanitize_device_name

# Check if psutil is available
PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None

if PSUTIL_AVAILABLE:
    import psutil


class NetworkDetector:
    """Detect network interfaces"""

    @staticmethod
    def _detect_interface_speed(iface_name: str, stats: dict) -> int:
        """
        Detect maximum interface speed in Mbps.

        Args:
            iface_name: Interface name
            stats: psutil network stats dictionary

        Returns:
            Speed in Mbps (0 if unknown)
        """
        speed_mbps = 0

        # Try to get supported link modes (max capability)
        ethtool_full = run_command(["ethtool", iface_name])
        if ethtool_full:
            # Look for "Supported link modes:" section and parse all speeds
            # Example: "10000baseT/Full", "2500baseT/Full", etc.
            speeds = re.findall(r"(\d+)base", ethtool_full)
            if speeds:
                speed_mbps = max(int(s) for s in speeds)

        # Fallback to psutil current link speed (only if ethtool completely failed)
        if speed_mbps == 0 and iface_name in stats:
            stat = stats[iface_name]
            speed_mbps = stat.speed if stat.speed > 0 else 0

        return speed_mbps

    @staticmethod
    def _format_speed(speed_mbps: int) -> str:
        """
        Format speed in Mbps to human-readable string.

        Args:
            speed_mbps: Speed in Mbps

        Returns:
            Formatted speed string (e.g., "10Gb/s", "1000Mb/s", "Unknown")
        """
        if speed_mbps >= MBPS_TO_GBPS_DIVISOR:
            return f"{speed_mbps / MBPS_TO_GBPS_DIVISOR}Gb/s"
        if speed_mbps > 0:
            return f"{speed_mbps}Mb/s"
        return "Unknown"

    @staticmethod
    def _get_pci_info(iface_name: str, pci_addr: str, iface_data: dict) -> None:
        """
        Get PCI hardware information for interface and update iface_data in place.

        Args:
            iface_name: Interface name
            pci_addr: Full PCI address (e.g., "0000:15:00.0")
            iface_data: Interface data dictionary to update
        """
        iface_data["pci_address"] = pci_addr

        # Get PCI IDs (vendor:device)
        pci_short = pci_addr.split(":", 1)[1]  # Remove domain (0000:)
        lspci_line = run_command(["lspci", "-nn", "-s", pci_short])
        if lspci_line:
            pci_ids = parse_pci_ids(lspci_line)
            if pci_ids:
                vendor_id, device_id = pci_ids
                iface_data["pci_ids"] = {
                    "vendor": vendor_id,
                    "device": device_id,
                    "full": f"{vendor_id}:{device_id}",
                }

            # Get subsystem ID
            lspci_verbose = run_command(["lspci", "-vnn", "-s", pci_short])
            subsystem_id = parse_subsystem_id(lspci_verbose)
            if subsystem_id:
                iface_data["subsystem_id"] = subsystem_id

        # Get IOMMU group (for passthrough)
        iommu_group = get_iommu_group(pci_addr)
        if iommu_group is not None:
            iface_data["iommu_group"] = iommu_group

        # Get device name/model from lspci
        if lspci_line:
            # Extract description between device type and vendor IDs
            desc_match = re.search(r":\s+(.+?)\s+\[", lspci_line)
            if desc_match:
                iface_data["device_name"] = desc_match.group(1).strip()

    @staticmethod
    def _detect_interface_with_psutil(iface_name: str, iface_addrs: list, stats: dict) -> dict[str, Any]:
        """
        Detect single network interface using psutil.

        Args:
            iface_name: Interface name
            iface_addrs: List of addresses for this interface
            stats: psutil network stats dictionary

        Returns:
            Interface data dictionary
        """
        iface_data = {"interface": iface_name, "type": "Ethernet"}

        # Get MAC and IPs
        for addr in iface_addrs:
            if addr.family == 2:  # IPv4
                iface_data["ipv4"] = addr.address
                iface_data["netmask"] = addr.netmask
            elif addr.family == 17:  # MAC
                iface_data["mac"] = addr.address

        # Get speed
        speed_mbps = NetworkDetector._detect_interface_speed(iface_name, stats)
        iface_data["speed"] = NetworkDetector._format_speed(speed_mbps)

        # Get link status
        if iface_name in stats:
            stat = stats[iface_name]
            iface_data["is_up"] = stat.isup

        # Get driver
        driver_path = Path(f"/sys/class/net/{iface_name}/device/driver")
        if driver_path.exists() and driver_path.is_symlink():
            try:
                driver = driver_path.resolve().name
                if driver:
                    iface_data["driver"] = driver
            except (OSError, RuntimeError):
                pass

        # Get PCI address (hardware location)
        device_path_link = Path(f"/sys/class/net/{iface_name}/device")
        if device_path_link.exists() and device_path_link.is_symlink():
            try:
                pci_addr_path = str(device_path_link.readlink())
                pci_addr = extract_pci_address_from_path(pci_addr_path)
                if pci_addr:
                    NetworkDetector._get_pci_info(iface_name, pci_addr, iface_data)
            except (OSError, RuntimeError):
                pass

        return iface_data

    @staticmethod
    def _detect_interfaces_psutil() -> list[dict[str, Any]]:
        """
        Detect all network interfaces using psutil.

        Returns:
            List of interface data dictionaries
        """
        interfaces = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, iface_addrs in addrs.items():
            if iface_name == "lo":
                continue

            # Sanitize interface name to prevent shell injection
            iface_name = sanitize_device_name(iface_name)
            if not iface_name:
                continue

            iface_data = NetworkDetector._detect_interface_with_psutil(iface_name, iface_addrs, stats)
            interfaces.append(iface_data)

        return interfaces

    @staticmethod
    def _detect_interfaces_fallback() -> list[dict[str, Any]]:
        """
        Detect network interfaces without psutil (fallback method).

        Returns:
            List of interface data dictionaries
        """
        interfaces = []
        ip_output = run_command(["ip", "-br", "addr", "show"])
        for line in ip_output.split("\n"):
            if "lo" in line or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                iface_name = parts[0]
                iface_data = {"interface": iface_name, "type": "Ethernet"}
                if len(parts) >= 3:
                    iface_data["ipv4"] = parts[2].split("/")[0]
                interfaces.append(iface_data)
        return interfaces

    @staticmethod
    def _get_pci_to_interface_map() -> dict[str, list[str]]:
        """
        Build a map of PCI addresses to Linux interface names.

        Scans /sys/class/net/*/device to find which interfaces
        correspond to which PCI devices.

        Returns:
            Dict mapping PCI address (e.g., "0000:08:00.0") to list of interface names
        """
        pci_to_iface: dict[str, list[str]] = {}

        net_path = Path("/sys/class/net")
        if not net_path.exists():
            return pci_to_iface

        for iface_dir in net_path.iterdir():
            iface_name = iface_dir.name
            if iface_name == "lo":
                continue

            device_link = iface_dir / "device"
            if device_link.exists() and device_link.is_symlink():
                try:
                    # The symlink points to something like:
                    # ../../../0000:08:00.0 or ../../devices/pci0000:00/.../0000:08:00.0
                    pci_path = str(device_link.readlink())
                    pci_addr = extract_pci_address_from_path(pci_path)
                    if pci_addr:
                        if pci_addr not in pci_to_iface:
                            pci_to_iface[pci_addr] = []
                        pci_to_iface[pci_addr].append(iface_name)
                except (OSError, RuntimeError):
                    pass

        return pci_to_iface

    @staticmethod
    def _detect_pcie_cards() -> list[dict[str, Any]]:
        """
        Detect PCIe network cards with their Linux interface names.

        Returns:
            List of PCIe network card data dictionaries including interface names
        """
        pcie_cards = []
        lspci_output = run_command(["lspci", "-nn"])

        # Build PCI address to interface name mapping
        pci_to_iface = NetworkDetector._get_pci_to_interface_map()

        # Filter network/ethernet devices
        pcie_nics = ""
        for line in lspci_output.split("\n"):
            line_lower = line.lower()
            if "network" in line_lower or "ethernet" in line_lower:
                pcie_nics += line + "\n"

        # Parse each network device
        for line in pcie_nics.split("\n"):
            if not line.strip():
                continue

            match = re.match(r"([0-9a-f:\.]+)\s+.*?:\s+(.+)\s+\[([0-9a-f]+):([0-9a-f]+)\]", line)
            if match:
                pci_addr, description, vendor_id, device_id = match.groups()
                full_pci_addr = f"0000:{pci_addr}"

                # Report ALL PCIe network cards (no filtering)
                card: dict[str, Any] = {
                    "name": description.strip(),
                    "pci_address": full_pci_addr,
                    "vendor_id": vendor_id,
                    "device_id": device_id,
                    "type": "10Gb Ethernet" if "10" in description else "Ethernet",
                }

                # Get Linux interface name(s) for this PCI device
                interfaces = pci_to_iface.get(full_pci_addr, [])
                if interfaces:
                    # Single interface - use 'interface' field
                    if len(interfaces) == 1:
                        card["interface"] = interfaces[0]
                    # Multiple interfaces (multi-port card) - use 'interfaces' list
                    else:
                        card["interfaces"] = sorted(interfaces)
                    # Also get driver from the first interface
                    first_iface = interfaces[0]
                    driver_path = Path(f"/sys/class/net/{first_iface}/device/driver")
                    if driver_path.exists() and driver_path.is_symlink():
                        with contextlib.suppress(OSError, RuntimeError):
                            card["driver"] = driver_path.resolve().name

                # Get subsystem ID (required for Proxmox PCIe mappings)
                lspci_verbose = run_command(["lspci", "-vnn", "-s", pci_addr])
                subsystem_id = parse_subsystem_id(lspci_verbose)
                if subsystem_id:
                    card["subsystem_id"] = subsystem_id

                # Get IOMMU group
                iommu_group = get_iommu_group(full_pci_addr)
                if iommu_group is not None:
                    card["iommu_group"] = iommu_group

                pcie_cards.append(card)

        return pcie_cards

    @staticmethod
    def _detect_current_network() -> dict[str, Any]:
        """
        Detect current network configuration (gateway, DNS).

        Returns:
            Current network configuration dictionary
        """
        current_network: dict[str, Any] = {}

        # Detect default gateway
        ip_route_output = run_command(["ip", "route", "show", "default"])
        default_route = ip_route_output.split("\n")[0] if ip_route_output else ""
        if default_route:
            parts = default_route.split()
            if "via" in parts:
                gateway_idx = parts.index("via") + 1
                if gateway_idx < len(parts):
                    current_network["gateway"] = parts[gateway_idx]
            if "dev" in parts:
                dev_idx = parts.index("dev") + 1
                if dev_idx < len(parts):
                    current_network["interface"] = parts[dev_idx]

        # Get DNS servers
        resolv_conf = run_command(["cat", "/etc/resolv.conf"])
        dns_servers_list = []
        for line in resolv_conf.split("\n"):
            if line.strip().startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2:
                    dns_servers_list.append(parts[1])
        if dns_servers_list:
            current_network["dns_servers"] = dns_servers_list

        return current_network

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect network interfaces, PCIe cards, and current network configuration"""
        # Detect interfaces
        if PSUTIL_AVAILABLE:
            interfaces = NetworkDetector._detect_interfaces_psutil()
        else:
            interfaces = NetworkDetector._detect_interfaces_fallback()

        # Detect PCIe network cards
        pcie_cards = NetworkDetector._detect_pcie_cards()

        # Detect current network configuration
        current_network = NetworkDetector._detect_current_network()

        return {
            "interfaces": interfaces,
            "pcie_cards": pcie_cards,
            "current_network": current_network,
        }
