"""Tests for logging setup module."""

import logging
from io import StringIO

from cgc_common.logging_setup import (
    ColoredFormatter,
    get_logger,
    set_level,
    setup_logging,
)


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging("test_app")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_app"

    def test_default_level_info(self):
        logger = setup_logging("test_info")
        assert logger.level == logging.INFO

    def test_custom_level_debug(self):
        logger = setup_logging("test_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_level_from_string(self):
        logger = setup_logging("test_str_level", level="WARNING")
        assert logger.level == logging.WARNING

    def test_logs_to_stream(self):
        stream = StringIO()
        logger = setup_logging("test_stream", stream=stream, colored=False)
        logger.info("Test message")
        output = stream.getvalue()
        assert "Test message" in output
        assert "test_stream" in output

    def test_log_format(self):
        stream = StringIO()
        logger = setup_logging("test_format", stream=stream, colored=False)
        logger.info("Hello")
        output = stream.getvalue()
        # Default format includes timestamp, level, name, message
        assert "INFO" in output
        assert "test_format" in output
        assert "Hello" in output

    def test_custom_format(self):
        stream = StringIO()
        logger = setup_logging(
            "test_custom_fmt",
            stream=stream,
            colored=False,
            format_string="%(levelname)s: %(message)s"
        )
        logger.info("Custom")
        output = stream.getvalue()
        assert output.strip() == "INFO: Custom"

    def test_file_logging(self, tmp_path):
        log_file = tmp_path / "app.log"
        logger = setup_logging("test_file", log_file=log_file, colored=False)
        logger.info("File log message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()

        content = log_file.read_text()
        assert "File log message" in content

    def test_file_creates_parent_dirs(self, tmp_path):
        log_file = tmp_path / "deep" / "nested" / "app.log"
        logger = setup_logging("test_nested", log_file=log_file)
        logger.info("Nested")
        for handler in logger.handlers:
            handler.flush()
        assert log_file.exists()

    def test_module_levels(self):
        stream = StringIO()
        setup_logging(
            "test_module_levels",
            stream=stream,
            colored=False,
            module_levels={"noisy_module": logging.ERROR}
        )
        noisy_logger = logging.getLogger("noisy_module")
        assert noisy_logger.level == logging.ERROR

    def test_clears_existing_handlers(self):
        # First setup
        logger = setup_logging("test_clear")
        initial_count = len(logger.handlers)

        # Second setup should not add more handlers
        logger = setup_logging("test_clear")
        assert len(logger.handlers) == initial_count

    def test_no_propagate(self):
        logger = setup_logging("test_propagate")
        assert logger.propagate is False


class TestColoredFormatter:
    def test_formatter_created(self):
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        assert formatter is not None

    def test_format_message(self):
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None
        )
        result = formatter.format(record)
        assert "Test" in result


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger("my.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "my.module"

    def test_child_logger(self):
        setup_logging("parent_app")
        child = get_logger("parent_app.submodule")
        assert child.name == "parent_app.submodule"


class TestSetLevel:
    def test_set_level_by_int(self):
        logger = setup_logging("test_setlevel_int")
        set_level("test_setlevel_int", logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_set_level_by_string(self):
        logger = setup_logging("test_setlevel_str")
        set_level("test_setlevel_str", "WARNING")
        assert logger.level == logging.WARNING

    def test_set_level_case_insensitive(self):
        logger = setup_logging("test_setlevel_case")
        set_level("test_setlevel_case", "error")
        assert logger.level == logging.ERROR
