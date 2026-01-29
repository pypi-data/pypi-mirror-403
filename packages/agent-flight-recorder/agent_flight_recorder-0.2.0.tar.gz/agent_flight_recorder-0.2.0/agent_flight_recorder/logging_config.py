"""
Logging configuration for Agent Flight Recorder.

Provides utilities for configuring logging throughout the application
with customizable levels, formats, and handlers.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional


class LoggingConfig:
    """Configure logging for Agent Flight Recorder."""
    
    # Log level constants
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(
        self,
        log_level: int = logging.INFO,
        log_dir: Optional[str] = None,
        log_file: bool = True,
        log_to_console: bool = True
    ) -> None:
        """
        Initialize logging configuration.
        
        Args:
            log_level: Minimum logging level (default: INFO)
            log_dir: Directory for log files (None = no file logging)
            log_file: Whether to log to file
            log_to_console: Whether to log to console
        """
        self.log_level = log_level
        self.log_dir = log_dir
        self.log_file = log_file
        self.log_to_console = log_to_console
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging handlers and formatters."""
        # Create root logger
        root_logger = logging.getLogger("agent_flight_recorder")
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers = []
        
        # Define format
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.log_file and self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
            
            # Main log file
            log_file_path = os.path.join(self.log_dir, "agent_flight_recorder.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Error log file
            error_log_path = os.path.join(self.log_dir, "agent_flight_recorder_errors.log")
            error_handler = logging.FileHandler(error_log_path)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(f"agent_flight_recorder.{name}")
    
    @staticmethod
    def enable_debug_logging() -> None:
        """Enable debug logging for the application."""
        root_logger = logging.getLogger("agent_flight_recorder")
        root_logger.setLevel(logging.DEBUG)
        
        for handler in root_logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    @staticmethod
    def disable_logging() -> None:
        """Disable all logging."""
        logging.getLogger("agent_flight_recorder").disabled = True
    
    @staticmethod
    def enable_logging() -> None:
        """Enable all logging."""
        logging.getLogger("agent_flight_recorder").disabled = False
    
    @staticmethod
    def set_level(level: int) -> None:
        """
        Set logging level.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        root_logger = logging.getLogger("agent_flight_recorder")
        root_logger.setLevel(level)
        
        for handler in root_logger.handlers:
            handler.setLevel(level)


# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"agent_flight_recorder.{name}")


def configure_logging(
    log_level: int = logging.INFO,
    log_dir: Optional[str] = None
) -> LoggingConfig:
    """
    Configure logging for Agent Flight Recorder.
    
    Args:
        log_level: Logging level
        log_dir: Directory for log files
        
    Returns:
        LoggingConfig instance
    """
    config = LoggingConfig(
        log_level=log_level,
        log_dir=log_dir,
        log_file=log_dir is not None
    )
    return config
