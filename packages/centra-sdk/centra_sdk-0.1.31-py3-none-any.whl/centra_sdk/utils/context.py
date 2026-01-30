import os
import httpx
import threading
import logging
import asyncio
from hashlib import md5
import json

from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field
from centra_sdk.models.connector.v1.operations.config import ConfigOpts
from centra_sdk.utils.log_handling import LoggingConfiguration
from centra_sdk.utils.option_values_handler import OptionValuesHandler

@dataclass
class IntegrationContext:
    """Context holding integration resources and configuration."""
    httpx_client: Optional[httpx.AsyncClient] = None
    logger: Optional[logging.Logger] = None
    component_id: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    schema: Optional[List[ConfigOpts]] = None
    dynamic_options_handler: OptionValuesHandler = field(default_factory=OptionValuesHandler)
    _is_closed: bool = field(default=False, init=False)
    tasks: List[Any] = field(default_factory=list, init=False)
    app_custom: Optional[Any] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.httpx_client is None:
            self.httpx_client = httpx.AsyncClient()
        if self.logger is None:
            self.logger = logging.getLogger('centra_sdk')
    
    async def close(self):
        """Properly close resources."""
        if not self._is_closed and self.httpx_client:
            await self.httpx_client.aclose()
            self._is_closed = True

    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def register_tasks(self, tasks) -> None:
        """Register tasks to be managed by the context."""
        if self.tasks is None:
            self.tasks = []
        existing_task_set = set(self.tasks)
        for task in tasks:
            if task not in existing_task_set:
                self.tasks.append(task)
            else:
                self.logger.warning(f"Task {task} is already registered and will not be added again.")

    def register_handlers(self, handlers: List[OptionValuesHandler]):
        self.logger.info(f"Registering {len(handlers)} option values handlers.")
        for handler in handlers:
            self.dynamic_options_handler.register_handler(handler)

    def verify_handlers_registered(self, schema: List[ConfigOpts]):
        self.dynamic_options_handler.verify_handlers_registered(schema)

    def get_dynamic_options(self, *args, **kwargs):
        return self.dynamic_options_handler.handle(*args, **kwargs)


class IntegrationContextApi:
    """Thread-safe singleton API for managing integration context."""
    CONTEXT: Optional[IntegrationContext] = None
    _lock = threading.RLock()

    @classmethod
    async def clean(cls) -> None:
        """Clean up resources and reset context."""
        with cls._lock:
            if cls.CONTEXT:
                await cls.CONTEXT.close()
                cls.CONTEXT = None

    @classmethod
    def context(cls) -> IntegrationContext:
        """Get or create the singleton context instance."""
        with cls._lock:
            if cls.CONTEXT is None:
                cls.CONTEXT = cls._build_context(cls._get_log_level())
            return cls.CONTEXT

    @classmethod
    def _build_context(cls, log_level: int) -> IntegrationContext:
        """Build a new context instance with proper configuration."""
        ctx = IntegrationContext()
        
        console = cls._get_log_console()
        # Configure logger with rotating file handler
        LoggingConfiguration.setup_logger(
            logger=ctx.logger,
            component_id=ctx.component_id,
            log_level=log_level,
            console=console,
        )

        return ctx

    @classmethod
    def client(cls) -> httpx.AsyncClient:
        """Get the HTTP client instance.
        
        Raises:
            RuntimeError: If context has been closed
        """
        ctx = cls.context()
        if ctx._is_closed:
            raise RuntimeError("Cannot access client: context has been closed")
        return ctx.httpx_client

    @classmethod
    def log(cls) -> logging.Logger:
        """Get the logger instance."""
        return cls.context().logger

    @classmethod
    def schema(cls) -> Optional[List[ConfigOpts]]:
        """Get the integration schema."""
        return cls.context().schema

    @classmethod
    def configuration(cls) -> Optional[Dict[str, Any]]:
        """Get the integration configuration."""
        return cls.context().configuration

    @classmethod
    def _calc_configuration_key(cls, configuration) -> str:
        conf_content = json.dumps(configuration, sort_keys=True).encode('utf-8')
        return md5(conf_content).hexdigest()

    @classmethod
    def current_configuration_key(cls) -> str:
        return cls._calc_configuration_key(cls.configuration())

    @classmethod
    def component_id(cls) -> Optional[str]:
        """Get the component ID."""
        return cls.context().component_id

    @classmethod
    def set_schema(cls, schema: List[ConfigOpts]) -> None:
        """Register schema of integration configuration.
        
        Args:
            schema: List of ConfigOpts defining the integration schema
            
        Example:
            set_schema([
                ConfigOpts(
                    name="api_url",
                    opt_type=OptType.OPT_STRING,
                    default_value="default",
                    description="Inventory API URL"
                ),
                # ...
            ])
        """

        # prior to registering schema, verify that all handlers are registered
        cls.context().verify_handlers_registered(schema)
        cls.context().schema = schema

    @classmethod
    def set_component_id(cls, component_id: str) -> None:
        """Set component_id that is used to identify integration on Centra side.
        
        Args:
            component_id: Unique identifier for this integration component
        """
        if not component_id:
            raise ValueError("component_id cannot be empty")

        ctx = cls.context()
        ctx.component_id = component_id

        # Reconfigure logger with the new component_id
        LoggingConfiguration.update_logger_component_id(
            logger=ctx.logger,
            component_id=component_id,
            log_level=ctx.logger.level,
        )

    @classmethod
    def set_configuration(cls, configuration: Dict[str, Any]) -> bool:
        """Set configuration as dict of Key: Value.
        
        Args:
            configuration: Configuration dictionary
            
        Example:
            set_configuration({
                'api_url': 'http://www.integration.com',
                'api_key': '<secret_key>'
            })
        """
        if not isinstance(configuration, dict):
            raise TypeError("configuration must be a dictionary")

        configuration_key = cls._calc_configuration_key(configuration)
        if cls.configuration() is None or cls.current_configuration_key() != configuration_key:
            cls.context().configuration = configuration
            return True
        return False

    @classmethod
    def set_app_custom(cls, app_custom: Any) -> None:
        cls.context().app_custom = app_custom

    @classmethod
    def get_app_custom(cls) -> Any:
        return cls.context().app_custom

    @classmethod
    def set_log_level(cls, level: Union[int, str]) -> None:
        """Set the log level for the SDK logger.
        
        Args:
            level: Log level (int or string like 'DEBUG', 'INFO', etc.)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        ctx = cls.context()
        ctx.logger.setLevel(level)

        # Update all handlers with the new log level
        for handler in ctx.logger.handlers:
            handler.setLevel(level)

    @classmethod
    def _get_log_level(cls) -> int:
        """Get log level from environment variable or default to INFO.
        
        Returns:
            int: The logging level
            
        Raises:
            ValueError: If environment variable contains invalid log level
        """
        level_name = os.getenv('CENTRA_SDK_LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, level_name, None)
        if level is None:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            raise ValueError(
                f"Invalid log level '{level_name}'. Valid levels are: {valid_levels}"
            )
        return level

    @classmethod
    def _get_log_console(cls) -> bool:
        """Get log console flag from environment variable or default to False.
        
        Returns:
            bool: Whether to enable console logging
        """
        return os.getenv('CENTRA_SDK_LOG_CONSOLE', 'false').lower() in ('true', '1', 'yes', 'on')

    @classmethod
    def register_tasks(cls, tasks) -> None:
        cls.context().register_tasks(tasks)

    @classmethod
    def register_handlers(cls, handlers: List[OptionValuesHandler]):
        cls.context().register_handlers(handlers)

    @classmethod
    def get_dynamic_options(cls, *args, **kwargs):
        """Get the dynamic options handler instance."""
        return cls.context().get_dynamic_options(*args, **kwargs)

    @classmethod
    def start_bg_tasks(cls) -> List[Any]:
        """Start all background tasks registered in the context.

        Returns:
            List of started tasks
        """
        ctx = cls.context()
        started_tasks = []
        for task in ctx.tasks:
            if asyncio.iscoroutinefunction(task):
                started_task = asyncio.create_task(task())
                started_tasks.append(started_task)
            else:
                ctx.logger.warning(f"Task {task} is not a coroutine function and cannot be started.")
        return started_tasks

    @classmethod
    def stop_bg_tasks(cls, tasks: List[Any]) -> None:
        """Stop all background tasks.

        Args:
            tasks: List of tasks to stop
        """
        for task in tasks:
            task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(task)
            except asyncio.CancelledError:
                cls.log().info("Background task cancelled.")
