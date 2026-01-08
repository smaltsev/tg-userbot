"""
Telegram Group Scanner - A Python application for monitoring Telegram groups.

This package provides functionality to authenticate with Telegram API,
scan group messages, filter relevant content, and store extracted information.
"""

__version__ = "1.0.0"
__author__ = "Telegram Scanner Team"

from .main import TelegramScanner
from .command_interface import CommandInterface, ScannerState, ScannerStatus, ScanningReport

__all__ = ["TelegramScanner", "CommandInterface", "ScannerState", "ScannerStatus", "ScanningReport"]