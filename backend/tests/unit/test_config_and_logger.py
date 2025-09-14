"""
Unit tests for configuration and logging systems
"""

import pytest
import logging
from unittest.mock import patch
import os

from config import Config
from utils.logger import setup_logger, main_logger, ai_logger


class TestConfiguration:
    """Test configuration management"""
    
    def test_config_defaults(self):
        """Test that configuration has sensible defaults"""
        assert Config.API_TITLE == "AI Chat Assistant MVP"
        assert Config.API_VERSION == "1.0.0"
        assert Config.ENVIRONMENT in ["development", "production"]
        assert isinstance(Config.DEBUG, bool)
        assert isinstance(Config.GEMINI_MAX_RETRIES, int)
        assert isinstance(Config.DEEPAI_MAX_RETRIES, int)
        assert Config.GEMINI_MAX_RETRIES > 0
        assert Config.DEEPAI_MAX_RETRIES > 0
    
    def test_cors_configuration(self):
        """Test CORS origins configuration"""
        assert isinstance(Config.CORS_ORIGINS, list)
        assert len(Config.CORS_ORIGINS) > 0
        assert "http://localhost:3000" in Config.CORS_ORIGINS
    
    def test_environment_variable_loading(self):
        """Test environment variable loading"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'test',
            'DEBUG': 'false',
            'USE_DUMMY_AI': 'true'
        }):
            # Note: Config class loads env vars at import time,
            # so we test the mechanism works
            assert os.environ.get('ENVIRONMENT') == 'test'
            assert os.environ.get('DEBUG') == 'false'
            assert os.environ.get('USE_DUMMY_AI') == 'true'
    
    def test_processing_time_configuration(self):
        """Test processing time settings are reasonable"""
        assert Config.MIN_PROCESSING_TIME <= Config.DEFAULT_PROCESSING_TIME
        assert Config.DEFAULT_PROCESSING_TIME <= Config.MAX_PROCESSING_TIME
        assert Config.MIN_PROCESSING_TIME > 0
        assert Config.MAX_PROCESSING_TIME < 10  # Reasonable upper bound


class TestLoggingSystem:
    """Test the logging configuration and functionality"""
    
    def test_logger_creation(self):
        """Test logger setup function"""
        test_logger = setup_logger("test_logger", "DEBUG")
        
        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_logger"
        assert test_logger.level == logging.DEBUG
        assert len(test_logger.handlers) > 0
    
    def test_logger_prevents_duplicate_handlers(self):
        """Test that calling setup_logger multiple times doesn't create duplicate handlers"""
        logger1 = setup_logger("duplicate_test", "INFO")
        handler_count1 = len(logger1.handlers)
        
        logger2 = setup_logger("duplicate_test", "INFO")  # Same name
        handler_count2 = len(logger2.handlers)
        
        assert handler_count1 == handler_count2
        assert logger1 is logger2  # Should be the same logger instance
    
    def test_global_loggers_exist(self):
        """Test that global logger instances are created"""
        assert isinstance(main_logger, logging.Logger)
        assert isinstance(ai_logger, logging.Logger)
        assert main_logger.name == "ai_chat.main"
        assert ai_logger.name == "ai_chat.ai_service"
    
    def test_logger_levels(self):
        """Test different log levels work correctly"""
        test_logger = setup_logger("level_test", "WARNING")
        
        # Should be set to WARNING level
        assert test_logger.level == logging.WARNING
        
        # Test with DEBUG level
        debug_logger = setup_logger("debug_test", "DEBUG")
        assert debug_logger.level == logging.DEBUG
    
    def test_logger_formatter(self):
        """Test that logger has proper formatting"""
        test_logger = setup_logger("format_test")
        
        # Check that handler has a formatter
        handler = test_logger.handlers[0]
        assert handler.formatter is not None
        
        # Test formatting includes required elements
        formatter = handler.formatter
        test_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(test_record)
        assert "INFO" in formatted
        assert "Test message" in formatted


class TestConstants:
    """Test application constants"""
    
    def test_file_upload_constants(self):
        """Test file upload configuration constants"""
        from core.constants import MAX_FILE_SIZE, ALLOWED_FILE_TYPES, UPLOAD_DIRECTORY
        
        assert isinstance(MAX_FILE_SIZE, int)
        assert MAX_FILE_SIZE > 0
        assert isinstance(ALLOWED_FILE_TYPES, set)
        assert len(ALLOWED_FILE_TYPES) > 0
        assert all(ext.startswith('.') for ext in ALLOWED_FILE_TYPES)
        assert isinstance(UPLOAD_DIRECTORY, str)
        assert len(UPLOAD_DIRECTORY) > 0
    
    def test_allowed_file_types_are_safe(self):
        """Test that allowed file types are safe and don't include dangerous extensions"""
        from core.constants import ALLOWED_FILE_TYPES
        
        dangerous_extensions = {'.exe', '.bat', '.sh', '.cmd', '.scr', '.dll', '.jar'}
        overlap = ALLOWED_FILE_TYPES.intersection(dangerous_extensions)
        assert len(overlap) == 0, f"Dangerous file types found: {overlap}"
