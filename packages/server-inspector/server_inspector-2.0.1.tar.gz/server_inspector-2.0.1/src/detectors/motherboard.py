"""Motherboard detection module"""

import os
from typing import Any

from src.utils import run_command


class MotherboardDetector:
    """Detect motherboard information"""

    @staticmethod
    def detect() -> dict[str, Any]:
        """Detect motherboard specifications"""
        mb_data = {}

        if os.geteuid() == 0:
            # Baseboard information
            manufacturer = run_command(["dmidecode", "-s", "baseboard-manufacturer"])
            product = run_command(["dmidecode", "-s", "baseboard-product-name"])
            version = run_command(["dmidecode", "-s", "baseboard-version"])
            serial = run_command(["dmidecode", "-s", "baseboard-serial-number"])

            if manufacturer and manufacturer not in ["", "To Be Filled By O.E.M."]:
                mb_data["manufacturer"] = manufacturer
            if product and product not in ["", "To Be Filled By O.E.M."]:
                mb_data["product_name"] = product
            if version and version not in ["", "To Be Filled By O.E.M."]:
                mb_data["version"] = version
            if serial and serial not in ["", "To Be Filled By O.E.M.", "Default string"]:
                mb_data["serial"] = serial

            # BIOS information
            bios_vendor = run_command(["dmidecode", "-s", "bios-vendor"])
            bios_version = run_command(["dmidecode", "-s", "bios-version"])
            bios_date = run_command(["dmidecode", "-s", "bios-release-date"])

            if bios_vendor:
                mb_data["bios_vendor"] = bios_vendor
            if bios_version:
                mb_data["bios_version"] = bios_version
            if bios_date:
                mb_data["bios_date"] = bios_date

            # Chassis information
            chassis_type = run_command(["dmidecode", "-s", "chassis-type"])
            if chassis_type and chassis_type != "Other":
                mb_data["chassis_type"] = chassis_type

        return mb_data
