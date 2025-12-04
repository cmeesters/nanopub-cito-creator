"""Test suite for utils.logger module."""
import pytest
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.utils.logger import setup_logger


class TestSetupLogger:
    """Test setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger()
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_with_default_log_file(self):
        """Test setup_logger uses default log file name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "nanopub_cito.log")
            with patch("src.utils.logger.logging.basicConfig") as mock_config:
                setup_logger(log_file)
                mock_config.assert_called_once()

    def test_setup_logger_with_custom_log_file(self):
        """Test setup_logger with custom log file name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "custom.log")
            # Create logger with custom file
            with patch("src.utils.logger.logging.basicConfig") as mock_config:
                setup_logger(log_file)
                call_args = mock_config.call_args[1]
                assert call_args["filename"] == log_file

    def test_setup_logger_sets_info_level(self):
        """Test that setup_logger sets INFO level."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            assert call_args["level"] == logging.INFO

    def test_setup_logger_sets_format(self):
        """Test that setup_logger sets correct log format."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            assert "format" in call_args
            # Check format contains expected fields
            fmt = call_args["format"]
            assert "%(asctime)s" in fmt
            assert "%(levelname)s" in fmt
            assert "%(message)s" in fmt

    def test_setup_logger_format_includes_timestamp(self):
        """Test that logger format includes timestamp."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            fmt = call_args["format"]
            assert "%(asctime)s" in fmt

    def test_setup_logger_format_includes_level(self):
        """Test that logger format includes log level."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            fmt = call_args["format"]
            assert "%(levelname)s" in fmt

    def test_setup_logger_format_includes_message(self):
        """Test that logger format includes message."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            fmt = call_args["format"]
            assert "%(message)s" in fmt


class TestSetupLoggerIntegration:
    """Integration tests for setup_logger."""

    def test_setup_logger_returns_valid_logger_instance(self):
        """Test that logger instance is valid and can be used."""
        logger = setup_logger()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')

    def test_setup_logger_is_root_logger(self):
        """Test that setup_logger returns the root logger."""
        logger = setup_logger()
        assert logger.name == 'root'

    def test_setup_logger_info_method_callable(self):
        """Test that logger.info method is callable."""
        logger = setup_logger()
        # Should not raise an exception
        logger.info("Test message")

    def test_setup_logger_multiple_calls(self):
        """Test that setup_logger can be called multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file1 = os.path.join(tmpdir, "log1.log")
            log_file2 = os.path.join(tmpdir, "log2.log")

            logger1 = setup_logger(log_file1)
            logger2 = setup_logger(log_file2)

            assert isinstance(logger1, logging.Logger)
            assert isinstance(logger2, logging.Logger)

    def test_setup_logger_with_path_containing_directories(self):
        """Test setup_logger with nested directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "logs", "nested")
            os.makedirs(nested_dir, exist_ok=True)
            log_file = os.path.join(nested_dir, "test.log")

            with patch("src.utils.logger.logging.basicConfig") as mock_config:
                setup_logger(log_file)
                call_args = mock_config.call_args[1]
                assert call_args["filename"] == log_file

    def test_setup_logger_returns_same_instance(self):
        """Test that setup_logger returns the default logger."""
        logger1 = setup_logger()
        logger2 = setup_logger()

        # Both should be the root logger
        assert logger1 is logger2


class TestSetupLoggerEdgeCases:
    """Test edge cases for setup_logger."""

    def test_setup_logger_with_empty_filename(self):
        """Test setup_logger with empty filename."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger("")
            mock_config.assert_called_once()

    def test_setup_logger_default_parameter(self):
        """Test that setup_logger has correct default parameter."""
        with patch("src.utils.logger.logging.basicConfig") as mock_config:
            setup_logger()
            call_args = mock_config.call_args[1]
            assert call_args["filename"] == "nanopub_cito.log"

    def test_setup_logger_with_special_characters_in_filename(self):
        """Test setup_logger with special characters in filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_log-2024.log")

            with patch("src.utils.logger.logging.basicConfig") as mock_config:
                setup_logger(log_file)
                call_args = mock_config.call_args[1]
                assert call_args["filename"] == log_file

    def test_setup_logger_with_absolute_path(self):
        """Test setup_logger with absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "absolute_path.log")
            log_file = os.path.abspath(log_file)

            with patch("src.utils.logger.logging.basicConfig") as mock_config:
                setup_logger(log_file)
                call_args = mock_config.call_args[1]
                assert os.path.isabs(call_args["filename"])
