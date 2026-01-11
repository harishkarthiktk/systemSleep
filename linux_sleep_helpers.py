"""Shared helper functions for Linux sleep management - function-based like config_loader.py"""
import os
import platform
import subprocess
from typing import Tuple


def check_linux_environment() -> Tuple[bool, str]:
    """
    Check if running on Linux with systemd support.
    Returns: (is_valid, error_message)
    """
    if platform.system().lower() != "linux":
        return False, "This script only supports Linux systems."

    if not os.path.exists('/run/systemd/system'):
        return False, "Systemd not detected. This script requires systemd."

    return True, ""


def check_sleep_permissions(sleep_type: str) -> Tuple[bool, str]:
    """
    Check if user has permission to execute sleep command using --dry-run.
    Returns: (has_permission, error_message)
    """
    if sleep_type not in ["suspend", "hibernate", "hybrid-sleep"]:
        return False, f"Invalid sleep type: {sleep_type}"

    try:
        result = subprocess.run(
            ["systemctl", sleep_type, "--dry-run"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return True, ""

        # Parse error for helpful message
        stderr = result.stderr.lower()
        if "authentication" in stderr or "unauthorized" in stderr:
            return False, (
                f"Insufficient permissions for {sleep_type}. "
                "Try running with sudo or configure polkit rules."
            )

        return False, f"Cannot use {sleep_type}: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, f"Permission check timed out for {sleep_type}"
    except FileNotFoundError:
        return False, "systemctl command not found"
    except Exception as e:
        return False, f"Permission check failed: {e}"


def get_sleep_command(sleep_type: str) -> list:
    """Get systemctl sleep command for given type."""
    commands = {
        "suspend": ["systemctl", "suspend"],
        "hibernate": ["systemctl", "hibernate"],
        "hybrid-sleep": ["systemctl", "hybrid-sleep"]
    }
    return commands.get(sleep_type, commands["suspend"])


def execute_sleep(sleep_type: str, timeout: int = 15) -> Tuple[bool, str]:
    """
    Execute sleep command with timeout protection.
    Returns: (success, error_message)
    """
    try:
        cmd = get_sleep_command(sleep_type)
        subprocess.run(cmd, check=True, timeout=timeout)
        return True, ""

    except subprocess.TimeoutExpired:
        return False, f"Sleep command timed out after {timeout} seconds."
    except subprocess.CalledProcessError as e:
        return False, f"Sleep command failed: {e}"
    except Exception as e:
        return False, f"Unexpected error during sleep: {e}"
