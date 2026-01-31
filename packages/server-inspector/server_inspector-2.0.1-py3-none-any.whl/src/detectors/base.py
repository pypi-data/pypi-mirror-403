"""Base detector abstract class"""

from abc import ABC, abstractmethod
from typing import Any


class BaseDetector(ABC):
    """Abstract base class for hardware detectors"""

    @staticmethod
    @abstractmethod
    def detect() -> dict[str, Any] | list[dict[str, Any]]:
        """Detect hardware and return specifications

        Returns:
            Dictionary or list of dictionaries containing hardware specifications
        """
        pass
