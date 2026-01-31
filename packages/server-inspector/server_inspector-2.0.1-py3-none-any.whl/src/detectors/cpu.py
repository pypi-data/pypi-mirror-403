"""CPU detection module"""

import importlib.util
import re
from typing import Any

from src.utils import run_command

# Check if psutil is available
PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None

if PSUTIL_AVAILABLE:
    import psutil


class CPUDetector:
    """Detect CPU information"""

    @staticmethod
    def _detect_iommu_support(cpu_manufacturer: str) -> dict[str, Any]:
        """Detect IOMMU hardware support and kernel status.

        Args:
            cpu_manufacturer: CPU manufacturer ("AMD" or "Intel")

        Returns:
            Dictionary with 'supported', 'enabled', and 'type' keys
        """
        # Check if CPU supports IOMMU (hardware capability)
        cpuinfo = run_command(["cat", "/proc/cpuinfo"])
        iommu_hw_support_intel = "vmx" in cpuinfo or "svm" in cpuinfo

        # Check if IOMMU is actually enabled in kernel (from dmesg)
        dmesg_output = run_command(["dmesg"], timeout=5)
        iommu_intel_enabled = "DMAR: IOMMU enabled" in dmesg_output
        iommu_amd_enabled = "AMD-Vi: Found IOMMU" in dmesg_output

        # Check kernel command line parameters
        cmdline = run_command(["cat", "/proc/cmdline"])
        iommu_cmdline = "intel_iommu=on" in cmdline or "amd_iommu=on" in cmdline

        # Determine IOMMU type and status based on manufacturer
        if "AMD" in cpu_manufacturer:
            return {
                "type": "AMD-Vi",
                "supported": True,  # AMD Ryzen supports IOMMU
                "enabled": bool(iommu_amd_enabled or iommu_cmdline),
            }
        if "Intel" in cpu_manufacturer:
            return {
                "type": "Intel VT-d",
                "supported": bool(iommu_hw_support_intel),
                "enabled": bool(iommu_intel_enabled or iommu_cmdline),
            }
        return {
            "type": "None",
            "supported": False,
            "enabled": False,
        }

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect CPU specifications"""
        cpu_data: dict[str, Any] = {}

        # Basic info from lscpu
        lscpu_output = run_command(["lscpu"])
        cpu_model = ""
        cpu_arch = ""
        vendor = ""

        for line in lscpu_output.split("\n"):
            if line.startswith("Model name:"):
                cpu_model = line.split(":", 1)[1].strip()
            elif line.startswith("Architecture:"):
                cpu_arch = line.split(":", 1)[1].strip()
            elif line.startswith("Vendor ID:"):
                vendor = line.split(":", 1)[1].strip()

        # Extract base clock from model name BEFORE cleaning (if present)
        # E.g., "AMD Ryzen 9 7900 ... Unknown CPU @ 3.7GHz"
        base_clock_from_name = None
        if cpu_model:
            match = re.search(r"@\s*([\d.]+)\s*GHz", cpu_model)
            if match:
                base_clock_from_name = f"{match.group(1)} GHz"

        # Clean up CPU model (remove duplicates and extra info)
        if cpu_model:
            # Remove "Unknown CPU @" patterns first
            cpu_model = re.sub(r"\s+Unknown CPU @ [\d.]+GHz", "", cpu_model).strip()
            # Check if model is duplicated (first half == second half)
            # This handles cases like "AMD Ryzen 9 7900 12-Core Processor AMD Ryzen 9 7900 12-Core Processor"
            words = cpu_model.split()
            if len(words) >= 4 and len(words) % 2 == 0:
                half = len(words) // 2
                first_half = " ".join(words[:half])
                second_half = " ".join(words[half:])
                if first_half == second_half:
                    cpu_model = first_half

        cpu_data["model"] = cpu_model
        cpu_data["architecture"] = cpu_arch
        cpu_data["manufacturer"] = "AMD" if "AMD" in vendor or "AuthenticAMD" in vendor else "Intel"

        # Core counts
        if PSUTIL_AVAILABLE:
            cpu_data["cores"] = psutil.cpu_count(logical=False)
            cpu_data["threads"] = psutil.cpu_count(logical=True)
        else:
            threads = ""
            cores_per_socket = ""
            sockets = ""
            for line in lscpu_output.split("\n"):
                if line.startswith("CPU(s):"):
                    threads = line.split(":", 1)[1].strip()
                elif line.startswith("Core(s) per socket:"):
                    cores_per_socket = line.split(":", 1)[1].strip()
                elif line.startswith("Socket(s):"):
                    sockets = line.split(":", 1)[1].strip()

            cpu_data["threads"] = int(threads) if threads.isdigit() else 0
            if cores_per_socket.isdigit() and sockets.isdigit():
                cpu_data["cores"] = int(cores_per_socket) * int(sockets)

        # Clock speeds
        max_mhz = ""
        for line in lscpu_output.split("\n"):
            if line.startswith("CPU max MHz:"):
                max_mhz = line.split(":", 1)[1].strip()
                break

        if max_mhz:
            from contextlib import suppress

            with suppress(ValueError):
                cpu_data["boost_clock"] = f"{float(max_mhz) / 1000:.1f} GHz"
        if base_clock_from_name:
            cpu_data["base_clock"] = base_clock_from_name

        # Virtualization support
        virt_check = ""
        for line in lscpu_output.split("\n"):
            if "Virtualization:" in line or "VT-x" in line or "AMD-V" in line:
                virt_check = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                break
        cpu_data["virtualization_supported"] = bool(virt_check)
        cpu_data["virtualization_type"] = virt_check if virt_check else "None"

        # IOMMU support - check both CPU capability and kernel status
        iommu_info = CPUDetector._detect_iommu_support(cpu_data.get("manufacturer", ""))
        cpu_data["iommu"] = iommu_info

        # Build features list
        cpu_data["features"] = []
        if cpu_data["virtualization_supported"]:
            cpu_data["features"].append("Virtualization")
        if iommu_info["supported"]:
            cpu_data["features"].append(iommu_info["type"])

        return cpu_data
