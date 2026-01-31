"""Tests for logger module."""

from pathlib import Path
import tempfile

from owlab.core.logger import get_logger
from owlab.core.logger import reset_logger_config


class TestLogger:
    """Tests for logger functionality."""

    def test_get_logger_default(self):
        """Test getting default logger."""
        logger = get_logger("test")
        assert logger is not None
        # Loguru logger doesn't have a 'name' attribute
        # Instead, we verify it's a logger instance by checking it can log
        logger.debug("Test debug message")
        assert hasattr(logger, "info")  # Verify it has logger methods

    def test_get_logger_with_file(self):
        """Test getting logger with file output."""
        reset_logger_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            log_file = f.name

        try:
            logger = get_logger("test_file", log_file=log_file)
            logger.info("Test message")
            assert Path(log_file).exists()
        finally:
            if Path(log_file).exists():
                Path(log_file).unlink()

    def test_get_logger_custom_level(self):
        """Test getting logger with custom level."""
        logger = get_logger("test_level", level="DEBUG")
        assert logger is not None

    def test_logger_output(self, capsys):
        """Test logger output."""
        reset_logger_config()
        logger = get_logger("test_output")
        logger.info("Test info message")
        captured = capsys.readouterr()
        assert "Test info message" in captured.err
