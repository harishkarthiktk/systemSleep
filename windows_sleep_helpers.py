"""Shared helper functions for Windows sleep management - function-based like config_loader.py"""
import subprocess
import ctypes
from typing import Tuple


SLEEP_COMMAND = ["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"]

# SetThreadExecutionState flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def execute_sleep(timeout: int = 15) -> Tuple[bool, str]:
    """
    Execute Windows sleep command with timeout protection.
    Returns: (success, error_message)
    """
    try:
        subprocess.run(SLEEP_COMMAND, check=True, timeout=timeout)
        return True, ""

    except subprocess.TimeoutExpired:
        return False, f"Sleep command timed out after {timeout} seconds."
    except subprocess.CalledProcessError as e:
        return False, f"Sleep command failed: {e}"
    except Exception as e:
        return False, f"Unexpected error during sleep: {e}"


def start_sleep_prevention() -> Tuple[bool, str]:
    """
    Prevent Windows sleep using SetThreadExecutionState API.
    Returns: (success, error_message)
    """
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        return True, ""
    except Exception as e:
        return False, f"Failed to prevent sleep: {e}"


def stop_sleep_prevention() -> Tuple[bool, str]:
    """
    Allow Windows sleep by resetting SetThreadExecutionState.
    Returns: (success, error_message)
    """
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        return True, ""
    except Exception as e:
        return False, f"Failed to allow sleep: {e}"
