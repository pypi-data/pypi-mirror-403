"""Utility functions for home server inspector."""

import re
import subprocess

try:
    from colors import Colors
except ImportError:
    from .colors import Colors


# Command and UI Constants
COMMAND_TIMEOUT_SECONDS = 10  # Default subprocess timeout
HEADER_WIDTH = 70  # Width of header lines
COMMON_RAM_SIZES_GB = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]  # Common RAM module sizes
RAM_SIZE_TOLERANCE_GB = 3  # Tolerance for matching common RAM sizes
TB_TO_GB_MULTIPLIER = 1000  # Convert TB to GB
MBPS_TO_GBPS_DIVISOR = 1000  # Convert Mb/s to Gb/s


def run_command(cmd: list[str] | str, timeout: int = COMMAND_TIMEOUT_SECONDS, shell: bool = False) -> str:
    """Execute command and return output

    Args:
        cmd: Command as list of arguments (preferred) or string (for shell pipelines only)
        timeout: Command timeout in seconds
        shell: Whether to use shell execution (only for complex pipelines with pipes/redirects)

    Returns:
        Command output as string, or empty string on error

    Note:
        Prefer list-based commands without shell=True for security.
        Only use shell=True when absolutely necessary for pipes/redirects.
    """
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)  # nosec B602
        return result.stdout.strip()
    except FileNotFoundError:
        # Command not found in PATH
        return ""
    except subprocess.TimeoutExpired:
        # Command took too long to execute
        return ""
    except subprocess.SubprocessError:
        # Other subprocess errors (CalledProcessError, etc.)
        return ""
    except OSError:
        # OS-level errors (permission denied, etc.)
        return ""


def sanitize_device_name(name: str) -> str:
    """Validate and sanitize device names to prevent shell injection

    Args:
        name: Device name from system (e.g., 'sda', 'nvme0n1')

    Returns:
        Sanitized name if valid, empty string if invalid

    Raises:
        ValueError: If name contains suspicious characters
    """
    # Device names should only contain alphanumeric chars, hyphens, underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        print_warning(f"Suspicious device name detected, skipping: {name}")
        return ""
    return name


def print_header(text: str) -> None:
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * HEADER_WIDTH}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^{HEADER_WIDTH}}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * HEADER_WIDTH}{Colors.END}\n")


def print_status(emoji: str, message: str) -> None:
    """Print status message"""
    print(f"{emoji} {message}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_success(message: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")
