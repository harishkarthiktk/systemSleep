#!/usr/bin/env python3
"""
Linux System Sleep Manager - supports both sleep scheduling and sleep prevention
Works with systemd-based distributions (Fedora, Ubuntu, Debian, Arch, openSUSE, RHEL)
"""

import os
import sys
import time
import platform
import subprocess
import argparse
import signal
from typing import Optional

import config_loader
import linux_sleep_helpers
import log_manager


# Global for prevent mode cleanup
prevent_process = None


def countdown_timer(minutes: int, logger, cycle: int = 1):
    """Display countdown timer with Ctrl+C handling"""
    total_seconds = minutes * 60
    try:
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            print(f"[Cycle {cycle}] Countdown: {mins:02d}:{secs:02d}", end="\r")
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        logger.info("Countdown interrupted by user.")
        sys.exit(0)


def sleep_system(sleep_type: str, logger: logging.Logger, timeout: int = 15) -> bool:
    """
    Put system to sleep using systemd.
    Returns: True if successful, False otherwise
    """
    logger.info(f"Issuing {sleep_type} command...")
    success, error = linux_sleep_helpers.execute_sleep(sleep_type, timeout)

    if success:
        logger.info(f"System {sleep_type} command issued successfully.")
        return True
    else:
        logger.error(f"Failed to put system to sleep: {error}")
        print(f"Failed to sleep: {error}")
        return False


def sleep_mode_loop(
    initial_delay: int,
    wake_delay: int,
    sleep_type: str,
    logger: logging.Logger,
    timeout: int
):
    """
    Multi-cycle sleep behavior - sleep, wake, wait, repeat
    (Following systemSleep.py pattern)
    """
    cycle = 1
    delay_minutes = initial_delay

    while True:
        if delay_minutes > 0:
            print(f"[Cycle {cycle}] Sleeping in {delay_minutes} minute(s)...")
            countdown_timer(delay_minutes, logger, cycle)
        else:
            print(f"[Cycle {cycle}] Sleeping immediately...")

        success = sleep_system(sleep_type, logger, timeout)
        if not success:
            logger.info("Sleep failed. Exiting.")
            print("Sleep failed. Exiting.")
            break

        print(f"[Cycle {cycle}] System woke up. Waiting {wake_delay} minutes before next sleep...")
        logger.info(f"System woke up. Starting {wake_delay}-minute delay before next sleep cycle.")
        delay_minutes = wake_delay
        cycle += 1


def start_sleep_prevention(reason: str, logger: logging.Logger) -> bool:
    """
    Start systemd-inhibit to prevent system sleep.
    (Following macDontSleep.py pattern with caffeinate-like subprocess)
    """
    global prevent_process

    try:
        inhibit_cmd = [
            "systemd-inhibit",
            "--what=sleep",
            "--who=linuxSleep",
            f"--why={reason}",
            "sleep", "infinity"
        ]

        prevent_process = subprocess.Popen(inhibit_cmd)
        logger.info(f"Sleep prevention started (PID: {prevent_process.pid}). Reason: {reason}")
        print(f"Sleep prevention activated (PID: {prevent_process.pid})")
        print(f"  Reason: {reason}")
        return True

    except FileNotFoundError:
        error_msg = "systemd-inhibit command not found"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Error starting sleep prevention: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return False


def stop_sleep_prevention(logger: logging.Logger):
    """Stop sleep prevention process"""
    global prevent_process

    if prevent_process:
        try:
            prevent_process.terminate()
            prevent_process.wait(timeout=2)
            logger.info("Sleep prevention stopped.")
            print("Sleep prevention deactivated")
        except Exception as e:
            logger.warning(f"Error stopping sleep prevention: {e}")
            print(f"Warning: Error stopping sleep prevention: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully (like macDontSleep.py)"""
    print("\n\nInterrupt received, shutting down...")
    stop_sleep_prevention(logger)
    print("Goodbye!")
    sys.exit(0)


def prevent_mode_loop(reason: str, logger: logging.Logger):
    """
    Run in prevent-sleep mode - keep inhibit alive until Ctrl+C
    (Following macDontSleep.py pattern)
    """
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"Starting sleep prevention mode. Reason: {reason}")

    if not start_sleep_prevention(reason, logger):
        logger.error("Failed to start sleep prevention")
        sys.exit(1)

    print("\n" + "="*60)
    print("System Sleep Prevention Active")
    print("="*60)
    print(f"Reason: {reason}")
    print("Press Ctrl+C to exit")
    print("="*60)

    try:
        # Keep script alive
        while prevent_process and prevent_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    finally:
        stop_sleep_prevention(logger)


def main():
    # Platform and systemd check
    valid, error = linux_sleep_helpers.check_linux_environment()
    if not valid:
        print(f"Error: {error}")
        sys.exit(1)

    # Load config
    config = config_loader.get_script_config("linux_sleep")

    # Setup CLI argument parsing
    parser = argparse.ArgumentParser(description="Linux System Sleep Manager")

    # Mode selection
    parser.add_argument(
        "--mode", "-m",
        choices=["sleep", "prevent"],
        default="sleep",
        help="Operation mode: 'sleep' for scheduling sleep, 'prevent' to block sleep"
    )

    # Sleep type (only for sleep mode)
    parser.add_argument(
        "--sleep-type", "-s",
        choices=["suspend", "hibernate", "hybrid-sleep"],
        help="Type of sleep (suspend/hibernate/hybrid-sleep)"
    )

    # Timing
    parser.add_argument(
        "--delay", "-d",
        type=int,
        help="Initial delay in minutes before sleep"
    )
    parser.add_argument(
        "--wake-delay", "-w",
        type=int,
        help="Delay after wake-up before next sleep cycle"
    )

    # Prevent mode settings
    parser.add_argument(
        "--prevent-reason",
        help="Reason for preventing sleep (shown in systemd logs)"
    )

    # Common settings
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        help="Sleep command timeout in seconds"
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Path to log file"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file"
    )

    args = parser.parse_args()

    # Merge config with CLI args (CLI takes precedence)
    mode = args.mode
    sleep_type = args.sleep_type or config.get("default_sleep_type", "suspend")
    log_file = args.log_file  # CLI overrides default
    timeout = args.timeout or config.get("sleep_command_timeout", 15)
    wake_delay = args.wake_delay or config.get("wake_delay_minutes", 5)
    default_delay = config.get("default_delay_minutes", 0)

    if args.delay is not None:
        default_delay = args.delay

    prevent_reason = args.prevent_reason or config.get(
        "prevent_sleep_reason",
        "User requested via linux_sleep.py"
    )

    # Initialize logger (global so signal handler can use it)
    global logger
    logger = log_manager.init_logger("linux_sleep", log_file)

    # Mode-specific logic
    if mode == "sleep":
        # Check permissions
        has_perm, perm_error = linux_sleep_helpers.check_sleep_permissions(sleep_type)
        if not has_perm:
            print(f"Error: {perm_error}")
            logger.error(perm_error)
            sys.exit(1)

        # Interactive mode (unless CLI args provided)
        if args.delay is None:
            selection = input(f"Put system to sleep ({sleep_type}) after a delay? (y/n): ")
            if selection.strip().lower() != 'y':
                print("Exiting.")
                sys.exit(0)

            try:
                delay = input(f"Enter delay before sleep in minutes ({default_delay} for default): ")
                if not delay.strip():
                    delay_minutes = default_delay
                else:
                    delay_minutes = int(delay)
                if delay_minutes < 0:
                    raise ValueError
            except ValueError:
                print("Invalid input. Please enter a non-negative integer.")
                sys.exit(1)
        else:
            delay_minutes = default_delay

        logger.info(f"Starting sleep mode: {sleep_type}, delay: {delay_minutes}m")
        sleep_mode_loop(delay_minutes, wake_delay, sleep_type, logger, timeout)

    elif mode == "prevent":
        logger.info(f"Starting prevent-sleep mode. Reason: {prevent_reason}")
        prevent_mode_loop(prevent_reason, logger)


if __name__ == "__main__":
    main()
