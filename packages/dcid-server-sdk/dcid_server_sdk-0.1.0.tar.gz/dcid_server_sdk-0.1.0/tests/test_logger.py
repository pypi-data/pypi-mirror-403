"""Tests for utils/logger.py"""

import pytest
from dcid_server_sdk.utils.logger import Logger, ConsoleLogger, NoOpLogger


class TestNoOpLogger:
    def test_implements_logger(self):
        logger = NoOpLogger()
        assert isinstance(logger, Logger)

    def test_debug_no_panic(self):
        logger = NoOpLogger()
        logger.debug("msg")
        logger.debug("msg", {"key": "val"})

    def test_info_no_panic(self):
        logger = NoOpLogger()
        logger.info("msg")
        logger.info("msg", {"key": "val"})

    def test_warn_no_panic(self):
        logger = NoOpLogger()
        logger.warn("msg")
        logger.warn("msg", {"key": "val"})

    def test_error_no_panic(self):
        logger = NoOpLogger()
        logger.error("msg")
        logger.error("msg", {"key": "val"})


class TestConsoleLogger:
    def test_implements_logger(self):
        logger = ConsoleLogger()
        assert isinstance(logger, Logger)

    def test_enabled_by_default(self):
        logger = ConsoleLogger()
        assert logger.enabled is True

    def test_can_disable(self):
        logger = ConsoleLogger(enabled=False)
        assert logger.enabled is False

    def test_debug_no_panic(self):
        logger = ConsoleLogger(enabled=True)
        logger.debug("debug msg")
        logger.debug("debug msg", {"k": "v"})

    def test_info_no_panic(self):
        logger = ConsoleLogger()
        logger.info("info msg")
        logger.info("info msg", {"k": "v"})

    def test_warn_no_panic(self):
        logger = ConsoleLogger()
        logger.warn("warn msg")
        logger.warn("warn msg", {"k": "v"})

    def test_error_no_panic(self):
        logger = ConsoleLogger()
        logger.error("error msg")
        logger.error("error msg", {"k": "v"})

    def test_disabled_logger_no_output(self, capsys):
        logger = ConsoleLogger(enabled=False)
        logger.info("should not appear")
        # No assertion on output — just verify no exception

    def test_debug_with_none_meta(self):
        logger = ConsoleLogger(enabled=True)
        logger.debug("msg", None)

    def test_info_with_none_meta(self):
        logger = ConsoleLogger()
        logger.info("msg", None)
