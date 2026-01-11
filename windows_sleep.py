import os
import sys
import time
import platform
import logging
import argparse
import signal

import config_loader
import windows_sleep_helpers

logger = None  # Global logger for signal handler


def init_logger(log_file: str = "sleep.log") -> logging.Logger:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def countdown_timer(minutes: int, logger: logging.Logger, cycle: int = 1):
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


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nInterrupt received, exiting...")
    if logger:
        logger.info("Program interrupted by user signal.")
    sys.exit(0)


def sleep_system(logger: logging.Logger, timeout: int = 15) -> bool:
    logger.info("Issuing sleep command...")
    success, error = windows_sleep_helpers.execute_sleep(timeout)

    if success:
        logger.info("System sleep command issued successfully.")
        return True
    else:
        logger.error(f"Failed to put system to sleep: {error}")
        print(f"Failed to sleep: {error}")
        return False


def is_run_as_pyw() -> bool:
    return sys.executable.lower().endswith("pythonw.exe") or sys.argv[0].lower().endswith(".pyw")


def main():
    if platform.system().lower() != "windows":
        print("This script only supports Windows 10 or higher.")
        sys.exit(1)

    # Load config
    config = config_loader.get_script_config("windows_sleep")

    # Setup CLI argument parsing
    parser = argparse.ArgumentParser(description="Windows System Sleep Scheduler")
    parser.add_argument("--delay", "-d", type=int,
                       help="Initial delay in minutes before sleep")
    parser.add_argument("--wake-delay", "-w", type=int,
                       help="Delay after wake-up before next sleep cycle")
    parser.add_argument("--timeout", "-t", type=int,
                       help="Sleep command timeout in seconds")
    parser.add_argument("--log-file", "-l",
                       help="Path to log file")
    parser.add_argument("--config", default="config.json",
                       help="Path to config file")
    args = parser.parse_args()

    # Merge config with CLI args (args take precedence)
    log_file = args.log_file or config.get("log_file", "sleep.log")
    timeout = args.timeout or config.get("sleep_command_timeout", 15)
    wake_delay = args.wake_delay or config.get("wake_delay_minutes", 5)
    default_delay = config.get("default_delay_minutes", 0)
    if args.delay is not None:
        default_delay = args.delay

    global logger
    logger = init_logger(log_file)

    # Register signal handler for graceful Ctrl+C exit
    signal.signal(signal.SIGINT, signal_handler)

    if is_run_as_pyw():
        logger.info("Running as .pyw - sleeping immediately and exiting after wake.")
        sleep_system(logger, timeout)
        logger.info("Exiting after initial sleep in .pyw mode.")
        sys.exit(0)

    try:
        selection = input("Put system to sleep after a delay? (y/n): ")
        if selection.strip().lower() != 'y':
            print("Exiting.")
            sys.exit(0)
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

    cycle = 1
    while True:
        if delay_minutes > 0:
            print(f"[Cycle {cycle}] Sleeping in {delay_minutes} minute(s)...")
            countdown_timer(delay_minutes, logger, cycle)
        else:
            print(f"[Cycle {cycle}] Sleeping immediately...")

        sleep_system(logger, timeout)

        print(f"[Cycle {cycle}] System woke up. Waiting {wake_delay} minutes before next sleep...")
        logger.info(f"System woke up. Starting {wake_delay}-minute delay before next sleep cycle.")
        delay_minutes = wake_delay
        cycle += 1


if __name__ == "__main__":
    main()
