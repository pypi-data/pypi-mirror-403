import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggingConfiguration:
    """Manages logging configuration with rotating file handlers."""

    LOG_DIR = "/var/log/guardicore"
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
    BACKUP_COUNT = 10
    DEFAULT_COMPONENT_ID = "unknown_id"

    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s [%(funcName)s]: %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    @classmethod
    def setup_logger(
        cls,
        logger: logging.Logger,
        component_id: Optional[str] = None,
        log_level: int = logging.INFO,
        console: bool = False,
    ) -> None:
        """Configure logger with rotating file handler.

        Args:
            logger: Logger instance to configure
            component_id: Component identifier for log file naming (defaults to 'unknown_id')
            log_level: Logging level (default: INFO)
        """
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        logger.setLevel(log_level)
        logger.propagate = False

        formatter = logging.Formatter(cls.LOG_FORMAT, datefmt=cls.DATE_FORMAT)

        # Setup file handler
        file_handler = cls._create_file_handler(component_id, formatter)
        if file_handler:
            logger.addHandler(file_handler)
        
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    @classmethod
    def _create_file_handler(
        cls,
        component_id: Optional[str],
        formatter: logging.Formatter
    ) -> Optional[RotatingFileHandler]:
        """Create a rotating file handler for the logger.

        Args:
            component_id: Component identifier for log file naming
            formatter: Logging formatter to use

        Returns:
            Configured RotatingFileHandler or None if setup fails
        """
        try:
            # Ensure log directory exists
            log_dir = Path(cls.LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Construct log file name
            component = component_id or cls.DEFAULT_COMPONENT_ID
            log_file = log_dir / f"integration.{component}.log"

            # Create rotating file handler
            file_handler = RotatingFileHandler(
                filename=str(log_file),
                maxBytes=cls.MAX_BYTES,
                backupCount=cls.BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)

            return file_handler

        except (PermissionError, OSError) as e:
            # Log to stderr if we can't create the file handler
            print(f"Warning: Unable to create log file handler: {e}", flush=True)
            return None

    @classmethod
    def update_logger_component_id(
        cls,
        logger: logging.Logger,
        component_id: str,
        log_level: Optional[int] = None,
    ) -> None:
        """Update logger configuration when component_id changes.

        This is typically called after onboarding when the component_id becomes available.

        Args:
            logger: Logger instance to reconfigure
            component_id: New component identifier
            log_level: Optional new log level (keeps current if None)
        """
        current_level = log_level if log_level is not None else logger.level
        cls.setup_logger(logger, component_id, current_level)

    @classmethod
    def get_log_file_path(cls, component_id: Optional[str] = None) -> Path:
        """Get the path to the current log file.

        Args:
            component_id: Component identifier (defaults to 'unknown_id')

        Returns:
            Path object pointing to the log file
        """
        component = component_id or cls.DEFAULT_COMPONENT_ID
        return Path(cls.LOG_DIR) / f"integration.{component}.log"
