"""Tests for the logging_config module."""

import logging
import os

import pytest

from openapi_ts_client.logging_config import (
    DATE_FORMAT,
    LOG_LEVEL_ENV_VAR,
    LOGGER_NAME,
    VERBOSE_FORMAT,
    get_logger,
    setup_logging,
)


@pytest.fixture(autouse=True)
def clean_logger_state():
    """Reset logger state before and after each test."""
    # Save original env var
    original_env = os.environ.get(LOG_LEVEL_ENV_VAR)

    # Clear env var and logger state before test
    if LOG_LEVEL_ENV_VAR in os.environ:
        del os.environ[LOG_LEVEL_ENV_VAR]
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)

    yield

    # Restore original env var after test
    if original_env is not None:
        os.environ[LOG_LEVEL_ENV_VAR] = original_env
    elif LOG_LEVEL_ENV_VAR in os.environ:
        del os.environ[LOG_LEVEL_ENV_VAR]
    # Clean up logger
    logger.handlers.clear()


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_returns_logger(self):
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        """Test that logger has correct name."""
        logger = setup_logging()
        assert logger.name == LOGGER_NAME

    def test_default_level_is_debug(self):
        """Test that default logging level is DEBUG."""
        logger = setup_logging()
        assert logger.level == logging.DEBUG

    def test_custom_level(self):
        """Test setting a custom logging level."""
        logger = setup_logging(level=logging.INFO)
        assert logger.level == logging.INFO

    def test_has_handler(self):
        """Test that logger has at least one handler."""
        logger = setup_logging()
        assert len(logger.handlers) > 0

    def test_no_propagation(self):
        """Test that logger does not propagate to root."""
        logger = setup_logging()
        assert logger.propagate is False

    def test_idempotent_setup(self):
        """Test that calling setup_logging multiple times doesn't add handlers."""
        logger = setup_logging()
        handler_count = len(logger.handlers)
        logger = setup_logging()
        assert len(logger.handlers) == handler_count


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_base_logger(self):
        """Test getting the base logger."""
        logger = get_logger()
        assert logger.name == LOGGER_NAME

    def test_get_child_logger(self):
        """Test getting a child logger."""
        logger = get_logger("child")
        assert logger.name == f"{LOGGER_NAME}.child"

    def test_get_nested_child_logger(self):
        """Test getting a nested child logger."""
        logger = get_logger("module.submodule")
        assert logger.name == f"{LOGGER_NAME}.module.submodule"

    def test_none_returns_base_logger(self):
        """Test that None returns base logger."""
        logger = get_logger(None)
        assert logger.name == LOGGER_NAME


class TestConstants:
    """Tests for module constants."""

    def test_logger_name_constant(self):
        """Test LOGGER_NAME constant."""
        assert LOGGER_NAME == "openapi_ts_client"

    def test_verbose_format_contains_timestamp(self):
        """Test that VERBOSE_FORMAT contains timestamp placeholder."""
        assert "%(asctime)s" in VERBOSE_FORMAT

    def test_verbose_format_contains_level(self):
        """Test that VERBOSE_FORMAT contains level placeholder."""
        assert "%(levelname)" in VERBOSE_FORMAT

    def test_verbose_format_contains_module(self):
        """Test that VERBOSE_FORMAT contains module placeholder."""
        assert "%(module)s" in VERBOSE_FORMAT

    def test_verbose_format_contains_function(self):
        """Test that VERBOSE_FORMAT contains function name placeholder."""
        assert "%(funcName)s" in VERBOSE_FORMAT

    def test_verbose_format_contains_line_number(self):
        """Test that VERBOSE_FORMAT contains line number placeholder."""
        assert "%(lineno)d" in VERBOSE_FORMAT

    def test_verbose_format_contains_message(self):
        """Test that VERBOSE_FORMAT contains message placeholder."""
        assert "%(message)s" in VERBOSE_FORMAT

    def test_date_format(self):
        """Test DATE_FORMAT constant."""
        assert "%Y" in DATE_FORMAT
        assert "%m" in DATE_FORMAT
        assert "%d" in DATE_FORMAT
        assert "%H" in DATE_FORMAT
        assert "%M" in DATE_FORMAT
        assert "%S" in DATE_FORMAT


class TestLoggingOutput:
    """Tests for actual logging output."""

    def test_logger_can_log(self):
        """Test that logger can actually log messages."""
        logger = setup_logging()
        # This should not raise any exceptions
        logger.debug("Test debug message")
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

    def test_child_logger_can_log(self):
        """Test that child logger can log messages."""
        setup_logging()
        child_logger = get_logger("test_child")
        # This should not raise any exceptions
        child_logger.debug("Test child logger message")
