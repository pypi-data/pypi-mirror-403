"""Unit tests for logger module."""

import logging
import tempfile
from pathlib import Path


from mdns_generator.logger import LoggerMixin, get_logger, setup_logger


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_default(self):
        """Test setting up logger with defaults."""
        logger = setup_logger(name="test_default")

        assert logger.name == "test_default"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

        # Cleanup
        logger.handlers.clear()

    def test_setup_logger_custom_level(self):
        """Test setting up logger with custom level."""
        logger = setup_logger(name="test_level", level="DEBUG")

        assert logger.level == logging.DEBUG

        # Cleanup
        logger.handlers.clear()

    def test_setup_logger_with_file(self):
        """Test setting up logger with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logger(name="test_file", log_file=str(log_file))

            logger.info("Test message")

            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

            # Cleanup
            logger.handlers.clear()

    def test_setup_logger_creates_parent_dirs(self):
        """Test that setup_logger creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "test.log"
            logger = setup_logger(name="test_dirs", log_file=str(log_file))

            logger.info("Test")

            assert log_file.parent.exists()

            # Cleanup
            logger.handlers.clear()

    def test_setup_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        logger1 = setup_logger(name="test_dup")
        handler_count = len(logger1.handlers)

        logger2 = setup_logger(name="test_dup")

        assert logger1 is logger2
        assert len(logger2.handlers) == handler_count

        # Cleanup
        logger1.handlers.clear()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_existing(self):
        """Test getting an existing logger."""
        setup_logger(name="test_existing")
        logger = get_logger(name="test_existing")

        assert logger.name == "test_existing"
        assert len(logger.handlers) >= 1

        # Cleanup
        logger.handlers.clear()

    def test_get_logger_new(self):
        """Test getting a new logger."""
        # Clear any existing logger first
        logging.getLogger("test_new_logger").handlers.clear()

        logger = get_logger(name="test_new_logger")

        assert logger.name == "test_new_logger"

        # Cleanup
        logger.handlers.clear()


class TestLoggerMixin:
    """Tests for LoggerMixin class."""

    def test_logger_property(self):
        """Test that logger property returns correct logger."""

        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger = obj.logger

        assert logger.name == "TestClass"

    def test_logger_is_cached(self):
        """Test that logger property returns same instance."""

        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger1 = obj.logger
        logger2 = obj.logger

        assert logger1 is logger2

        # Cleanup
        logger1.handlers.clear()
