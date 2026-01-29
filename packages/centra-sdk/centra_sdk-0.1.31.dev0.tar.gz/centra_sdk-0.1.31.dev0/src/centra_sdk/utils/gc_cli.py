#!/usr/bin/env python3
"""
CLI interface for Claroty integration.

This module provides command-line tools for testing and managing
the Claroty integration outside of the FastAPI server context.

"""

import json
import sys
import click
import os
import tarfile
import io
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Union, Literal, Optional
from rich.console import Console

from rich import print as rprint
from click import pass_context
from rich.table import Table

from centra_sdk.models.connector.v1.operations.config import ConfigOpts
from centra_sdk.models.connector.v1.operations.onboard import IntegrationCapabilities, InfraCapabilities

# Constants
OUTPUT_FORMAT_TABLE = 'table'
OUTPUT_FORMAT_JSON = 'json'
STATUS_OK = 'okay'
STATUS_ERROR = 'error'
METADATA_FOLDER = 'metadata'

# Type aliases
OutputFormat = Literal['table', 'json']

console = Console()


@dataclass
class CliResponse(ABC):
    """Base class for CLI response data."""
    status: str
    message: str

    @property
    @abstractmethod
    def value(self) -> Union[Dict[str, Any], List]:
        """Convert to dictionary for JSON serialization."""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """Convert to dictionary for JSON serialization."""
        pass

    def print(self, format: str = 'json'):
        response_fmt = self.format(format)
        if isinstance(response_fmt, Table):
            rprint(response_fmt)
        else:
            print(response_fmt)

    def format(self, output_format: OutputFormat) -> Union[Table, str]:
        """Format the schema fields based on the requested output format."""

        if output_format == OUTPUT_FORMAT_JSON:
            return json.dumps(self.value)

        # table format
        if output_format == OUTPUT_FORMAT_TABLE:
            return self.format_table(self.value)

        return self.value

    def format_table(self, value) -> Union[Table, str]:
        table = Table(title=self.title)
        if isinstance(value, list):
            for i, raw in enumerate(value):
                if not i:
                    # build schema from first entry
                    for field in raw:
                        table.add_column(field.capitalize(), style="cyan")
                table.add_row(*[str(raw[field]) for field in raw])
        return table


@dataclass
class DiscoverMetadataResponse(CliResponse):
    metadata_archive_base64: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def title(self) -> str:
        return "Metadata"

    @property
    def value(self) -> List[Dict[str, Any]]:
        """Get the schema fields as serializable data.

        Returns:
            List of dictionaries containing schema field information
        """
        if self.status == STATUS_ERROR:
            return {"status": self.status, "message": self.message}

        return {
            "metadata_archive_base64": self.metadata_archive_base64,
            "metadata": self.metadata
        }

    @classmethod
    def success(cls, metadata_archive_base64: str, metadata: Dict) -> 'DiscoverMetadataResponse':
        return cls(
            status=STATUS_OK,
            message="Metadata discovery successful",
            metadata_archive_base64=metadata_archive_base64,
            metadata=metadata
        )

    @classmethod
    def error(cls, error_message: str, metadata_archive_base64: Optional[str] = None) -> 'DiscoverMetadataResponse':
        return cls(
            status=STATUS_ERROR,
            message=error_message
        )

    def format(self, output_format: OutputFormat) -> Union[Table, str]:
        if output_format == OUTPUT_FORMAT_TABLE:
            metadata_list = [{"key": k, "value": str(v)} for k, v in self.metadata.items()] if self.metadata else []
            return super().format_table(metadata_list)

        return super().format(output_format)

@dataclass
class DiscoverSchemaResponse(CliResponse):
    """Response wrapper for schema discovery operations.

    Encapsulates the result of discovering configuration schema fields,
    including the list of ConfigOpts objects that define the available
    configuration parameters.

    Attributes:
        schema_fields: List of configuration option definitions
    """
    schema_fields: List[ConfigOpts]

    @property
    def title(self) -> str:
        """Get the title for table display.

        Returns:
            Title string for schema table output
        """
        return "Configuration Schema"

    @classmethod
    def success(cls, schema_fields: List[ConfigOpts]) -> 'DiscoverSchemaResponse':
        """Create a successful schema discovery response.

        Args:
            schema_fields: List of discovered configuration options

        Returns:
            DiscoverSchemaResponse instance with success status
        """
        return cls(
            status=STATUS_OK,
            message="Schema discovery successful",
            schema_fields=schema_fields
        )

    @classmethod
    def error(cls, error_message: str, schema_fields: List[ConfigOpts] = None) -> 'DiscoverSchemaResponse':
        """Create an error schema discovery response.

        Args:
            error_message: Description of the error that occurred
            schema_fields: Optional partial schema fields (defaults to empty list)

        Returns:
            DiscoverSchemaResponse instance with error status
        """
        return cls(
            status=STATUS_ERROR,
            message=error_message,
            schema_fields=schema_fields or []
        )

    @property
    def value(self) -> List[Dict[str, Any]]:
        """Get the schema fields as serializable data.

        Returns:
            List of dictionaries containing schema field information
        """
        return [field.model_dump(mode='json') for field in self.schema_fields]


@dataclass
class HealthCheckResponse(CliResponse):
    """Response wrapper for health check operations.

    Encapsulates the result of performing a health check on the integration,
    including validation results, connectivity status, and diagnostic details.

    Attributes:
        details: Additional diagnostic information and context
    """
    details: Dict[str, Any]

    @property
    def title(self) -> str:
        """Get the title for table display.

        Returns:
            Title string for health check table output
        """
        return "Health check"

    @classmethod
    def success(cls, input_config: Dict[str, Any]) -> 'HealthCheckResponse':
        """Create a successful health check response.

        Args:
            input_config: The configuration that was validated successfully

        Returns:
            HealthCheckResponse instance with success status
        """
        return cls(
            status=STATUS_OK,
            message="Health check successful", 
            details={'input_config': input_config}
        )

    @classmethod
    def error(cls, error_message: str, details: Dict[str, Any] = None) -> 'HealthCheckResponse':
        """Create an error health check response.

        Args:
            error_message: Description of the health check failure
            details: Optional additional error context and diagnostic info

        Returns:
            HealthCheckResponse instance with error status
        """
        return cls(
            status=STATUS_ERROR,
            message=error_message,
            details=details or {}
        )

    @property
    def value(self) -> Dict[str, Any]:
        """Get the complete health check result as serializable data.
        
        Returns:
            Dictionary containing status, message, and diagnostic details
        """
        return {
            "status": self.status,
            "message": self.message,
            "details": self.details
        }


@dataclass
class DiscoverIntegrationCapabilitiesResponse(CliResponse):
    """Response wrapper for integration capabilities discovery operations.

    Encapsulates the result of discovering integration capabilities,
    including the list of capabilities that the integration supports.

    Attributes:
        capabilities: List of integration capabilities
    """
    capabilities: List[IntegrationCapabilities]

    @property
    def title(self) -> str:
        """Get the title for table display.

        Returns:
            Title string for integration capabilities table output
        """
        return "Integration Capabilities"

    @classmethod
    def success(cls, capabilities: List[IntegrationCapabilities]) -> 'DiscoverIntegrationCapabilitiesResponse':
        """Create a successful integration capabilities discovery response.

        Args:
            capabilities: List of discovered integration capabilities

        Returns:
            DiscoverIntegrationCapabilitiesResponse instance with success status
        """
        return cls(
            status=STATUS_OK,
            message="Integration capabilities discovery successful",
            capabilities=capabilities
        )

    @classmethod
    def error(cls, error_message: str, capabilities: List[IntegrationCapabilities] = None) -> 'DiscoverIntegrationCapabilitiesResponse':
        """Create an error integration capabilities discovery response.

        Args:
            error_message: Description of the error that occurred
            capabilities: Optional partial capabilities (defaults to empty list)

        Returns:
            DiscoverIntegrationCapabilitiesResponse instance with error status
        """
        return cls(
            status=STATUS_ERROR,
            message=error_message,
            capabilities=capabilities or []
        )

    @property
    def value(self) -> List[str]:
        """Get the integration capabilities as serializable data.

        Returns:
            List of capability values (strings)
        """
        return [cap.value for cap in self.capabilities]

    def print(self, format: str = 'json'):
        """Print the response in the specified format.

        Args:
            format: Output format ('json' or 'table')
        """
        response_fmt = self.format(format)
        if isinstance(response_fmt, Table):
            rprint(response_fmt)
        else:
            print(response_fmt)

    def format(self, output_format: OutputFormat) -> Union[Table, str]:
        """Format the capabilities based on the requested output format.

        Args:
            output_format: Desired output format

        Returns:
            Formatted output as Table or JSON string
        """
        if output_format == OUTPUT_FORMAT_JSON:
            if self.status == STATUS_ERROR:
                return json.dumps({"status": self.status, "message": self.message})
            return json.dumps({"status": self.status, "message": self.message, "capabilities": self.value})

        # table format
        if output_format == OUTPUT_FORMAT_TABLE:
            return self.format_table(self.value)

        return self.value

@dataclass
class DiscoverInfraCapabilitiesResponse(CliResponse):
    """Response wrapper for infrastructure capabilities discovery operations.

    Encapsulates the result of discovering infrastructure capabilities,
    including the list of capabilities that the integration supports.

    Attributes:
        capabilities: List of infrastructure capabilities
    """
    capabilities: List[InfraCapabilities]

    @property
    def title(self) -> str:
        """Get the title for table display.

        Returns:
            Title string for infrastructure capabilities table output
        """
        return "Infrastructure Capabilities"

    @classmethod
    def success(cls, capabilities: List[InfraCapabilities]) -> 'DiscoverInfraCapabilitiesResponse':
        """Create a successful infrastructure capabilities discovery response.

        Args:
            capabilities: List of discovered infrastructure capabilities

        Returns:
            DiscoverInfraCapabilitiesResponse instance with success status
        """
        return cls(
            status=STATUS_OK,
            message="Infrastructure capabilities discovery successful",
            capabilities=capabilities
        )

    @classmethod
    def error(cls, error_message: str, capabilities: List[InfraCapabilities] = None) -> 'DiscoverInfraCapabilitiesResponse':
        """Create an error infrastructure capabilities discovery response.

        Args:
            error_message: Description of the error that occurred
            capabilities: Optional partial capabilities (defaults to empty list)

        Returns:
            DiscoverInfraCapabilitiesResponse instance with error status
        """
        return cls(
            status=STATUS_ERROR,
            message=error_message,
            capabilities=capabilities or []
        )

    @property
    def value(self) -> List[str]:
        """Get the infrastructure capabilities as serializable data.

        Returns:
            List of capability values (strings)
        """
        return [cap.value for cap in self.capabilities]

    def print(self, format: str = 'json'):
        """Print the response in the specified format.

        Args:
            format: Output format ('json' or 'table')
        """
        response_fmt = self.format(format)
        if isinstance(response_fmt, Table):
            rprint(response_fmt)
        else:
            print(response_fmt)

    def format(self, output_format: OutputFormat) -> Union[Table, str]:
        """Format the capabilities based on the requested output format.

        Args:
            output_format: Desired output format

        Returns:
            Formatted output as Table or JSON string
        """
        if output_format == OUTPUT_FORMAT_JSON:
            if self.status == STATUS_ERROR:
                return json.dumps({"status": self.status, "message": self.message})
            return json.dumps({"status": self.status, "message": self.message, "capabilities": self.value})

        # table format
        if output_format == OUTPUT_FORMAT_TABLE:
            return self.format_table(self.value)

        return self.value

class CliHandler(ABC):
    """Abstract base class for CLI command handlers.
    
    This class defines the interface that all concrete CLI handlers must implement.
    It provides the contract for schema discovery and health check operations,
    ensuring consistent behavior across different integration implementations.
    
    Concrete implementations should inherit from this class and provide
    specific logic for their integration type (e.g., Claroty, ServiceNow, etc.).
    """

    CLI_NAME = None

    @abstractmethod
    def discover_schema_handler(self) -> DiscoverSchemaResponse:
        """Handle schema discovery command.
        
        Discovers and returns the configuration schema for the integration,
        including all available configuration parameters, their types,
        default values, and descriptions.
        
        Returns:
            DiscoverSchemaResponse containing the discovered schema information
            
        Raises:
            Exception: If schema discovery fails due to configuration or system errors
        """
        pass

    @abstractmethod
    def health_check_handler(self, input_config: dict) -> HealthCheckResponse:
        """Handle health check command.

        Validates the provided configuration and tests connectivity to the
        target integration. This may include API authentication, endpoint
        availability, and permission validation.

        Args:
            input_config: Dictionary containing the configuration to validate

        Returns:
            HealthCheckResponse containing the validation results and diagnostic info

        Raises:
            Exception: If health check fails due to invalid configuration or system errors
        """
        pass

    @abstractmethod
    def discover_integration_capabilities(self) -> DiscoverIntegrationCapabilitiesResponse:
        """Handle integration capabilities discovery command.

        Discovers and returns the list of integration capabilities that this
        connector supports (e.g., inventory, enforcement, asset discovery).

        Returns:
            DiscoverIntegrationCapabilitiesResponse containing the capabilities list

        Raises:
            Exception: If capabilities discovery fails due to configuration or system errors
        """
        pass

    @abstractmethod
    def discover_infra_capabilities(self) -> DiscoverInfraCapabilitiesResponse:
        """Handle infrastructure capabilities discovery command.

        Discovers and returns the list of infrastructure capabilities that this
        connector supports (e.g., agent-based, agentless, cloud-native).

        Returns:
            DiscoverInfraCapabilitiesResponse containing the capabilities list

        Raises:
            Exception: If capabilities discovery fails due to configuration or system errors
        """
        pass

    def discover_metadata(self) -> DiscoverMetadataResponse:
        try:
            self._validate_metadata_folder(METADATA_FOLDER)
            archive = self._archive_metadata_folder(METADATA_FOLDER)
            metadata = self._load_metadata_from_folder(METADATA_FOLDER)
            return DiscoverMetadataResponse.success(archive, metadata)
        except Exception as e:
            return DiscoverMetadataResponse.error(f"Error during metadata discovery: {e}")

    @staticmethod
    def _validate_metadata_folder(source_folder):
        """Validate that the source folder contains required files."""
        if not os.path.isdir(source_folder):
            raise ValueError(f"Source folder '{source_folder}' does not exist or is not a directory.")
        if not os.path.exists(f'{source_folder}/metadata.json'):
            raise ValueError(f"Source folder '{source_folder}' does not contain 'metadata.json' file.")
        if not os.path.exists(f'{source_folder}/icon.png'):
            raise ValueError(f"Source folder '{source_folder}' does not contain 'icon.png' file.")

    @staticmethod
    def _archive_metadata_folder(source_folder):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
            for root, _, files in os.walk(source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    # arcname is the path within the zip file
                    arcname = os.path.relpath(file_path, source_folder)
                    tar.add(file_path, arcname=arcname)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @staticmethod
    def _load_metadata_from_folder(source_folder) -> Dict[str, Any]:
        """Load metadata.json from the source folder."""
        metadata_path = os.path.join(source_folder, 'metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return metadata

    @classmethod
    def from_context(cls, ctx) -> 'CliHandler':
        """Extract the CLI handler from the Click context.

        Args:
            ctx: Click context object containing the handler in ctx.obj['handler']

        Returns:
            The CLI handler instance from the context
        """
        return ctx.obj['handler']

    @classmethod
    def create_cli(cls):
        if not cls.CLI_NAME:
            raise ValueError("CLI_NAME must be defined in the subclass")
        cli = create_cli(cls(), prog_name=cls.CLI_NAME)
        return cli


def _discover_schema_command():
    """Create the discover-schema command function."""
    @click.command()
    @click.option('--format', 'output_format', type=click.Choice([OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_JSON]),
                 default=OUTPUT_FORMAT_JSON, help='Output format')
    @pass_context
    def discover_schema(ctx, output_format: OutputFormat):
        """Discover and display the configuration schema for the integration.

        This command queries the integration to discover all available configuration
        parameters, including their types, default values, and descriptions. The output
        can be formatted as either a human-readable table or machine-parseable JSON.

        Args:
            output_format: The desired output format ('table' for console display, 'json' for programmatic use)

        Examples:
            # Display schema as a table
            cli discover-schema

            # Get schema as JSON for automation
            cli discover-schema --format json
        """
        try:
            ret = CliHandler.from_context(ctx).discover_schema_handler()
            ret.print(output_format)
        except Exception as e:
            ret = DiscoverSchemaResponse.error(f"Error while discovering schema: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
    return discover_schema


def _health_check_command():
    """Create the health-check command function."""
    @click.command()
    @click.option('--config', 'input_config', required=True, help='Config credentials (JSON)')
    @pass_context
    def health_check(ctx, input_config: str):
        """Perform a health check on the integration configuration.

        This command validates the provided configuration and tests connectivity
        to the target integration. It verifies authentication, endpoint availability,
        and basic functionality to ensure the integration is properly configured.

        Args:
            input_config: JSON string containing the configuration to validate

        Examples:
            # Check configuration from command line
            cli health-check --config '{"platform_url": "https://...", "platform_key": "..."}'
        """
        try:
            config = json.loads(input_config)
            ret = CliHandler.from_context(ctx).health_check_handler(config)
            ret.print(OUTPUT_FORMAT_JSON)
        except json.JSONDecodeError as e:
            ret = HealthCheckResponse.error(f"Invalid JSON input: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
        except Exception as e:
            ret = HealthCheckResponse.error(f"Error while verifying health check: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
    return health_check


def _discover_metadata_command():
    """Create the discover-schema command function."""
    @click.command()
    @click.option('--format', 'output_format', type=click.Choice([OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_JSON]), 
                 default=OUTPUT_FORMAT_JSON, help='Output format')
    @pass_context
    def discover_metadata(ctx, output_format: OutputFormat):
        try:
            ret = CliHandler.from_context(ctx).discover_metadata()
            ret.print(output_format)
        except Exception as e:
            ret = DiscoverSchemaResponse.error(f"Error while discovering metadata: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
    return discover_metadata


def _discover_integration_capabilities_command():
    """Create the discover-integration-capabilities command function."""
    @click.command()
    @click.option('--format', 'output_format', type=click.Choice([OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_JSON]),
                 default=OUTPUT_FORMAT_JSON, help='Output format')
    @pass_context
    def discover_integration_capabilities(ctx, output_format: OutputFormat):
        """Discover and display the integration capabilities.

        This command retrieves the list of integration capabilities that the
        connector supports, such as inventory, enforcement, asset discovery, etc.

        Examples:
            # Display capabilities in JSON format
            cli discover-integration-capabilities --format json

            # Display capabilities in table format
            cli discover-integration-capabilities --format table
        """
        try:
            ret = CliHandler.from_context(ctx).discover_integration_capabilities()
            ret.print(output_format)
        except Exception as e:
            ret = DiscoverIntegrationCapabilitiesResponse.error(f"Error while discovering integration capabilities: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
    return discover_integration_capabilities


def _discover_infra_capabilities_command():
    """Create the discover-infra-capabilities command function."""
    @click.command()
    @click.option('--format', 'output_format', type=click.Choice([OUTPUT_FORMAT_TABLE, OUTPUT_FORMAT_JSON]),
                 default=OUTPUT_FORMAT_JSON, help='Output format')
    @pass_context
    def discover_infra_capabilities(ctx, output_format: OutputFormat):
        """Discover and display the infrastructure capabilities.

        This command retrieves the list of infrastructure capabilities that the
        connector supports, such as agent-based, agentless, cloud-native, etc.

        Examples:
            # Display capabilities in JSON format
            cli discover-infra-capabilities --format json

            # Display capabilities in table format
            cli discover-infra-capabilities --format table
        """
        try:
            ret = CliHandler.from_context(ctx).discover_infra_capabilities()
            ret.print(output_format)
        except Exception as e:
            ret = DiscoverInfraCapabilitiesResponse.error(f"Error while discovering infrastructure capabilities: {e}")
            ret.print(OUTPUT_FORMAT_JSON)
            sys.exit(1)
    return discover_infra_capabilities


def get_default_commands() -> List[click.Command]:
    """Get the default CLI commands.
    
    Returns:
        List of default commands including schema, health-check, metadata, and capabilities discovery

    Example:
        # Get default commands for customization
        commands = get_default_commands()
        commands.append(my_custom_command())
        app = create_cli(handler, "my-cli", commands=commands)
    """
    return [
        _discover_schema_command(),
        _health_check_command(),
        _discover_metadata_command(),
        _discover_integration_capabilities_command(),
        _discover_infra_capabilities_command()
    ]


def create_cli(handler: 'CliHandler', prog_name: str = "cli", commands: Optional[List[click.Command]] = None):
    """Factory function to create a CLI with a specific handler and program name.
    
    Args:
        handler: The CLI handler instance that implements the abstract methods
        prog_name: The program name to display in help and version info
        commands: Optional list of custom commands to add (defaults to standard commands)
        
    Returns:
        Configured Click group ready to run
        
    Example:
        handler = MyCliHandler()
        app = create_cli(handler, "my-cli")
        app()
        
        # Or with custom commands
        custom_commands = [_discover_schema_command(), my_custom_command()]
        app = create_cli(handler, "my-cli", commands=custom_commands)
    """
    @click.group(name="cli")
    @click.version_option(version="1.0.0", prog_name=prog_name)
    @pass_context
    def cli_group(ctx):
        ctx.ensure_object(dict)
        ctx.obj['handler'] = handler

    # Add commands to the group (use defaults if none provided)
    if commands is None:
        commands = get_default_commands()
    
    for command in commands:
        cli_group.add_command(command)

    return cli_group
