#!/usr/bin/env python3
"""
Windows System Sleep Prevention using SetThreadExecutionState API
Prevents system sleep while keeping the process running
"""

import sys
import time
import signal
import argparse

import config_loader
import log_manager
import windows_sleep_helpers

# Global variables
logger = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nInterrupt received, shutting down...")
    if logger:
        logger.info("Program interrupted by user signal.")
    stop_sleep_prevention()
    print("Goodbye!")
    sys.exit(0)


def start_sleep_prevention():
    """Start preventing system sleep"""
    success, error = windows_sleep_helpers.start_sleep_prevention()

    if success:
        msg = "Sleep prevention activated (SetThreadExecutionState running)"
        print(f"{msg}")
        if logger:
            logger.info(msg)
        return True
    else:
        msg = f"Failed to prevent sleep: {error}"
        print(f"Error: {msg}")
        if logger:
            logger.error(msg)
        return False


def stop_sleep_prevention():
    """Stop sleep prevention"""
    success, error = windows_sleep_helpers.stop_sleep_prevention()

    if success:
        msg = "Sleep prevention deactivated"
        print(f"{msg}")
        if logger:
            logger.info(msg)
    else:
        msg = f"Error stopping sleep prevention: {error}"
        print(f"Warning: {msg}")
        if logger:
            logger.warning(msg)


def main():
    """Main program loop"""
    global logger

    # Load config
    config = config_loader.get_script_config("windows_prevent_sleep")

    # Setup CLI argument parsing
    parser = argparse.ArgumentParser(description="Windows System Sleep Prevention")
    parser.add_argument("--interval", "-i", type=int,
                       help="Check interval in seconds (for monitoring)")
    parser.add_argument("--log-file", "-l",
                       help="Path to log file")
    parser.add_argument("--config", default="config.json",
                       help="Path to config file")
    args = parser.parse_args()

    # Initialize logger
    log_file = args.log_file
    logger = log_manager.init_logger("windows_prevent_sleep", log_file)
    logger.info("Sleep prevention started")

    # Merge config with CLI args
    check_interval = args.interval or config.get("check_interval_seconds", 10)

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("Windows System Sleep Prevention")
    print("=" * 60)
    print("Press Ctrl+C to exit")
    print("=" * 60)

    if not start_sleep_prevention():
        logger.error("Failed to start sleep prevention")
        sys.exit(1)

    try:
        while True:
            time.sleep(check_interval)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        msg = f"Fatal error: {e}"
        print(f"\nError: {msg}")
        logger.error(msg)
        stop_sleep_prevention()
        sys.exit(1)
    finally:
        stop_sleep_prevention()


if __name__ == "__main__":
    main()
