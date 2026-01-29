"""Tool definition - Single Source of Truth."""

from dataclasses import dataclass, field
from typing import Any, Callable, Type

from .params import Param
from .sections import OutputDefinition


@dataclass
class ServiceConfig:
    """Service configuration for a tool."""

    service_class: Type  # e.g., GoogleService
    method: str  # e.g., "get_serp"

    # Required environment variables (for error messages)
    required_env: list[str] = field(default_factory=list)  # e.g., ["SERPER_API_KEY"]

    # Optional environment variables (will use empty string if not set)
    optional_env: list[str] = field(default_factory=list)  # e.g., ["DEVTO_API_KEY"]

    # Cache settings
    cache_ttl: int = 24 * 3600  # Default 24h in seconds


@dataclass
class ToolDefinition:
    """
    Complete tool definition - SSOT for CLI, MCP, and rendering.

    Example:
        google_serp = ToolDefinition(
            name="google_serp",
            description="Analyze Google SERP results",
            group="google",  # CLI group

            params=[QUERY, NUM_RESULTS, COUNTRY, NO_CACHE],

            service=ServiceConfig(
                service_class=GoogleService,
                method="get_serp",
                required_env=["SERPER_API_KEY"],
            ),

            output=OutputDefinition(
                title_template='Top Results: "{query}"',
                sections=[
                    TableSection(
                        data_path="results",
                        columns=[
                            position_column(),
                            title_column(),
                            domain_column(key="link"),
                        ],
                    ),
                ],
            ),
        )
    """

    # Identity
    name: str  # Unique identifier (e.g., "google_serp")
    description: str  # Used in CLI help and MCP tool description
    group: str  # CLI command group (e.g., "google", "devto", "reddit")

    # Parameters
    params: list[Param] = field(default_factory=list)

    # Service binding
    service: ServiceConfig | None = None

    # Output rendering
    output: OutputDefinition | None = None

    # Optional customization
    cli_name: str | None = None  # Override CLI command name (default: last part of name)
    mcp_enabled: bool = True  # Register as MCP tool
    cli_enabled: bool = True  # Register as CLI command

    # For tools that need custom logic
    custom_handler: Callable[..., Any] | None = None  # Override default service call
    custom_renderer: Callable[..., None] | None = None  # Override default rendering

    # MCP-specific
    mcp_name: str | None = None  # Override MCP tool name (default: name)

    @property
    def cli_command_name(self) -> str:
        """Get CLI command name."""
        if self.cli_name:
            return self.cli_name
        # Extract last part: "google_serp" -> "serp"
        return self.name.split("_")[-1] if "_" in self.name else self.name

    @property
    def mcp_tool_name(self) -> str:
        """Get MCP tool name."""
        return self.mcp_name or self.name

    def get_param(self, name: str) -> Param | None:
        """Get parameter by name."""
        for p in self.params:
            if p.name == name:
                return p
        return None

    def required_params(self) -> list[Param]:
        """Get required parameters."""
        return [p for p in self.params if p.required]

    def optional_params(self) -> list[Param]:
        """Get optional parameters."""
        return [p for p in self.params if not p.required]

    def to_mcp_schema(self) -> dict:
        """Generate MCP tool schema."""
        properties = {}
        required = []

        for param in self.params:
            properties[param.name] = param.to_mcp_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.mcp_tool_name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
