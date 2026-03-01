"""Unit tests for logging configuration."""
import logging
from unittest.mock import patch, MagicMock

from app.core.logging import configure_logging, get_logger


def test_configure_logging_runs():
    """configure_logging should not raise."""
    configure_logging()


def test_configure_logging_sets_root_level():
    configure_logging()
    root = logging.getLogger()
    assert root.level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)


def test_get_logger_returns_logger():
    logger = get_logger("test_module")
    assert logger is not None


def test_get_logger_no_name():
    logger = get_logger()
    assert logger is not None


def test_configure_logging_suppresses_verbose_loggers():
    configure_logging()
    uvicorn_access = logging.getLogger("uvicorn.access")
    assert uvicorn_access.level >= logging.WARNING


def test_configure_logging_debug_mode():
    with patch("app.core.logging.settings") as mock_settings:
        mock_settings.log_level = "DEBUG"
        mock_settings.debug = True
        configure_logging()
