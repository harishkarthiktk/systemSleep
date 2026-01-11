"""Shared helper functions for Windows sleep management - function-based like config_loader.py"""
import subprocess
from typing import Tuple


SLEEP_COMMAND = ["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"]


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
