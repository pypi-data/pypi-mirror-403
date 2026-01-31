"""Memory detection module"""

import importlib.util
import math
import os
import re
from typing import Any

from src.utils import COMMON_RAM_SIZES_GB, RAM_SIZE_TOLERANCE_GB, print_warning, run_command

# Check if psutil is available
PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None

if PSUTIL_AVAILABLE:
    import psutil


class MemoryDetector:
    """Detect memory information"""

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect memory specifications"""
        mem_data = {}

        # Total memory - round to common RAM sizes for better display
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            mem_gb_raw = mem.total / (1024**3)
            # Round to nearest common RAM size if close (e.g., 62 -> 64, 31 -> 32)
            for size in COMMON_RAM_SIZES_GB:
                if abs(mem_gb_raw - size) <= RAM_SIZE_TOLERANCE_GB:
                    mem_data["total_gb"] = size
                    break
            else:
                # No common size match, just round up
                mem_data["total_gb"] = int(math.ceil(mem_gb_raw))
        else:
            meminfo = run_command(["cat", "/proc/meminfo"])
            total_kb = ""
            for line in meminfo.split("\n"):
                if line.startswith("MemTotal:"):
                    total_kb = line.split()[1]
                    break
            if total_kb.isdigit():
                mem_gb_raw = int(total_kb) / 1024 / 1024
                # Round to nearest common RAM size if close
                for size in COMMON_RAM_SIZES_GB:
                    if abs(mem_gb_raw - size) <= RAM_SIZE_TOLERANCE_GB:
                        mem_data["total_gb"] = size
                        break
                else:
                    mem_data["total_gb"] = int(math.ceil(mem_gb_raw))

        # Detailed module info (requires root)
        if os.geteuid() == 0:
            modules = []
            dmidecode_out = run_command(["dmidecode", "-t", "memory"])

            current_module: dict[str, Any] = {}
            for line in dmidecode_out.split("\n"):
                line = line.strip()

                if line.startswith("Memory Device"):
                    if current_module and current_module.get("size"):
                        modules.append(current_module)
                    current_module = {}
                elif ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()

                    if key == "size" and value not in ["No Module Installed", "Not Installed"]:
                        current_module["size"] = value
                    elif key == "type" and value != "Unknown":
                        current_module["type"] = value
                    elif key == "speed" and value != "Unknown":
                        current_module["speed"] = value
                    elif key == "manufacturer" and value not in ["NO DIMM", "Unknown"]:
                        current_module["manufacturer"] = value
                    elif key == "locator":
                        current_module["slot"] = value

            if current_module and current_module.get("size"):
                modules.append(current_module)

            mem_data["slots_used"] = len(modules)

            # Get total slots - count Memory Device entries
            total_slots = dmidecode_out.count("Memory Device")
            if total_slots > 0:
                mem_data["slots_total"] = total_slots

            if modules:
                mem_data["type"] = modules[0].get("type", "Unknown")
                mem_data["speed"] = modules[0].get("speed", "Unknown")

            # ECC support - find first Error Correction Type line
            ecc_check = ""
            for line in dmidecode_out.split("\n"):
                if "Error Correction Type:" in line:
                    ecc_check = line.split(":", 1)[1].strip()
                    break
            mem_data["ecc"] = ecc_check not in ["None", "Unknown", ""] if ecc_check else False

            # Expandability
            if mem_data.get("slots_total") and mem_data.get("slots_used"):
                empty_slots = mem_data["slots_total"] - mem_data["slots_used"]
                if empty_slots > 0 and mem_data.get("total_gb") and modules:
                    # Calculate per-module size from actual module (e.g., "32 GB")
                    first_module_size = modules[0].get("size", "")
                    size_match = re.search(r"(\d+)\s*GB", first_module_size)
                    if size_match:
                        per_module_gb = float(size_match.group(1))
                        max_possible = per_module_gb * mem_data["slots_total"]
                        mem_data["expandable_to_gb"] = int(max_possible)
                    else:
                        # Fallback: use current total divided by slots
                        per_module_gb = float(mem_data["total_gb"]) / mem_data["slots_used"]
                        max_possible = per_module_gb * mem_data["slots_total"]
                        mem_data["expandable_to_gb"] = int(max_possible)
        else:
            print_warning("Not running as root - limited memory details available")

        return mem_data
