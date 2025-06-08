import os
import sys
import time
import platform
import subprocess
import logging
from typing import Optional

LOG_FILE = "sleep.log"
SLEEP_COMMAND = ["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"]


def init_logger() -> logging.Logger:
    logging.basicConfig(
        filename=LOG_FILE,
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


def sleep_system(logger: logging.Logger) -> bool:
    logger.info("Issuing sleep command...")
    try:
        subprocess.run(SLEEP_COMMAND, check=True)
        logger.info("System sleep command issued successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to put system to sleep: {e}")
        print(f"Failed to sleep: {e}")
        return False


def is_run_as_pyw() -> bool:
    return sys.executable.lower().endswith("pythonw.exe") or sys.argv[0].lower().endswith(".pyw")


def main():
    if platform.system().lower() != "windows":
        print("This script only supports Windows 10 or higher.")
        sys.exit(1)

    logger = init_logger()

    if is_run_as_pyw():
        logger.info("Running as .pyw - sleeping immediately and exiting after wake.")
        sleep_system(logger)
        logger.info("Exiting after initial sleep in .pyw mode.")
        sys.exit(0)

    try:
        selection = input("Put system to sleep after a delay? (y/n): ")
        if selection.strip().lower() != 'y':
            print("Exiting.")
            sys.exit(0)
        delay = input("Enter delay before sleep in minutes (0 for immediate): ")
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

        sleep_system(logger)

        print(f"[Cycle {cycle}] System woke up. Waiting 5 minutes before next sleep...")
        logger.info(f"System woke up. Starting 5-minute delay before next sleep cycle.")
        delay_minutes = 5
        cycle += 1


if __name__ == "__main__":
    main()
