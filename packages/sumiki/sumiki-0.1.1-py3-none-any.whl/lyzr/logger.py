"""
Internal logger for Lyzr SDK

Provides configurable logging for SDK operations.
"""

import logging
import sys
from typing import Literal, Any, Dict

LogLevel = Literal["debug", "info", "warning", "error", "none"]


class LyzrLogger:
    """
    Internal logger for Lyzr SDK

    Provides structured logging with configurable levels.
    """

    def __init__(self, level: str = "warning"):
        self.logger = logging.getLogger("lyzr")
        self.logger.propagate = False  # Don't propagate to root logger

        # Create console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.set_level(level)

    def set_level(self, level: str):
        """
        Set logging level

        Args:
            level: Log level (debug, info, warning, error, none)
        """
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "none": logging.CRITICAL + 1  # Above CRITICAL = silent
        }
        log_level = level_map.get(level.lower(), logging.WARNING)
        self.logger.setLevel(log_level)

    def debug(self, message: str, data: Any = None):
        """
        Log debug message with optional structured data

        Args:
            message: Log message
            data: Optional dict/object to pretty-print
        """
        if data is not None:
            import json
            try:
                json_str = json.dumps(data, indent=2, default=str)
                self.logger.debug(f"{message}\n{json_str}")
            except:
                self.logger.debug(f"{message}\n{data}")
        else:
            self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)


# Global logger instance
_logger: LyzrLogger = None


def get_logger() -> LyzrLogger:
    """
    Get global logger instance

    Returns:
        LyzrLogger: Global logger
    """
    global _logger
    if _logger is None:
        _logger = LyzrLogger()
    return _logger


def set_log_level(level: str):
    """
    Set global log level

    Args:
        level: Log level (debug, info, warning, error, none)
    """
    get_logger().set_level(level)
