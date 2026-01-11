"""Shared logging utility for all programs - function-based like config_loader.py"""
import os
import logging
from typing import Optional


def init_logger(program_name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize file-based logger for a program.

    Args:
        program_name: Name of the program (e.g., 'windows_sleep', 'linux_sleep_gui')
        log_file: Optional custom log file path. If not provided, uses logs/{program_name}.log

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    # Determine log file path
    if log_file is None:
        log_file = os.path.join(logs_dir, f"{program_name}.log")

    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    return logging.getLogger(program_name)
