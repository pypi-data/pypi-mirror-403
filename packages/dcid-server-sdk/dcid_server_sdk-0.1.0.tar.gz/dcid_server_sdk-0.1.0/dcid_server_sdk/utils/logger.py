"""Logger interface and implementations for SDK logging"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
import os


class Logger(ABC):
    """Logger interface for SDK logging"""

    @abstractmethod
    def debug(self, message: str, meta: Optional[Any] = None) -> None:
        """Log debug message"""
        pass

    @abstractmethod
    def info(self, message: str, meta: Optional[Any] = None) -> None:
        """Log info message"""
        pass

    @abstractmethod
    def warn(self, message: str, meta: Optional[Any] = None) -> None:
        """Log warning message"""
        pass

    @abstractmethod
    def error(self, message: str, meta: Optional[Any] = None) -> None:
        """Log error message"""
        pass


class ConsoleLogger(Logger):
    """Console-based logger implementation"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logging.getLogger("DCID SDK")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[DCID SDK] %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, message: str, meta: Optional[Any] = None) -> None:
        if self.enabled and os.getenv("PYTHON_ENV") != "production":
            if meta:
                self.logger.debug(f"{message} {meta}")
            else:
                self.logger.debug(message)

    def info(self, message: str, meta: Optional[Any] = None) -> None:
        if self.enabled:
            if meta:
                self.logger.info(f"{message} {meta}")
            else:
                self.logger.info(message)

    def warn(self, message: str, meta: Optional[Any] = None) -> None:
        if self.enabled:
            if meta:
                self.logger.warning(f"{message} {meta}")
            else:
                self.logger.warning(message)

    def error(self, message: str, meta: Optional[Any] = None) -> None:
        if self.enabled:
            if meta:
                self.logger.error(f"{message} {meta}")
            else:
                self.logger.error(message)


class NoOpLogger(Logger):
    """No-op logger implementation (disabled logging)"""

    def debug(self, message: str, meta: Optional[Any] = None) -> None:
        pass

    def info(self, message: str, meta: Optional[Any] = None) -> None:
        pass

    def warn(self, message: str, meta: Optional[Any] = None) -> None:
        pass

    def error(self, message: str, meta: Optional[Any] = None) -> None:
        pass
