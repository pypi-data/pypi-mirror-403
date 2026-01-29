"""Factories for generating CLI commands and MCP tools from definitions."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Annotated
from inspect import Parameter as InspectParam, Signature

from cyclopts import App, Parameter

from .tool import ToolDefinition
from .params import ParamType, Param
from .renderer import render


# =============================================================================
# Service Factory
# =============================================================================


_cache_instance = None


def get_cache():
    """Get singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        from ..services import CacheService

        _cache_instance = CacheService()
    return _cache_instance


def create_service(tool: ToolDefinition) -> Any | None:
    """
    Create service instance for a tool.

    Returns None if required env vars are missing.
    """
    if not tool.service:
        return None

    from ..config import load_env_config

    env = load_env_config()

    # Build kwargs for service constructor
    kwargs: dict[str, Any] = {"cache": get_cache()}

    # Map environment variables to constructor kwargs
    env_to_kwarg = {
        "SERPER_API_KEY": "api_key",
        "SEARCH_API_IO_KEY": "api_key",
        "SEARCHAPI_KEY": "api_key",
        "DEVTO_API_KEY": "api_key",
        "PERPLEXITY_API_KEY": "perplexity_api_key",
        "OPENAI_API_KEY": "openai_api_key",
    }

    def _get_env_value(env_key: str) -> str | None:
        """Get env value, trying alternative key formats."""
        value = env.get(env_key)
        if not value:
            alt_keys = [
                env_key.replace("_api_key", "_key"),
                env_key.replace("_key", "_api_key"),
                env_key.replace("search_api_io", "searchapi"),
            ]
            for alt in alt_keys:
                value = env.get(alt)
                if value:
                    break
        return value

    # Process required env vars
    for env_var in tool.service.required_env:
        value = _get_env_value(env_var.lower())
        if not value:
            return None  # Missing required key
        kwarg_name = env_to_kwarg.get(env_var.upper(), "api_key")
        kwargs[kwarg_name] = value

    # Process optional env vars (use empty string if not set)
    for env_var in tool.service.optional_env:
        value = _get_env_value(env_var.lower()) or ""
        kwarg_name = env_to_kwarg.get(env_var.upper(), "api_key")
        kwargs[kwarg_name] = value

    return tool.service.service_class(**kwargs)


def _parse_param_value(param, value: Any) -> Any:
    """Parse parameter value based on type and parser."""
    if value is None:
        return param.default

    # Use custom parser if defined
    if param.parser and isinstance(value, str):
        return param.parser(value)

    # Handle LIST type without custom parser
    if param.type == ParamType.LIST and isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]

    # Convert to proper type
    if param.type == ParamType.INT and not isinstance(value, int):
        return int(value)
    if param.type == ParamType.FLOAT and not isinstance(value, float):
        return float(value)
    if param.type == ParamType.BOOL and not isinstance(value, bool):
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)

    return value


# =============================================================================
# MCP Factory
# =============================================================================


def _param_to_python_type(param: Param) -> type:
    """Convert Param to Python type."""
    mapping = {
        ParamType.STRING: str,
        ParamType.INT: int,
        ParamType.BOOL: bool,
        ParamType.FLOAT: float,
        ParamType.ENUM: str,
        ParamType.LIST: str,  # Comma-separated string
    }
    return mapping[param.type]


def _create_mcp_handler(tool: ToolDefinition):
    """Create MCP handler function with proper signature for FastMCP."""
    # Build signature parameters
    sig_params = []
    for param in tool.params:
        py_type = _param_to_python_type(param)
        if param.required:
            sig_params.append(
                InspectParam(param.name, InspectParam.POSITIONAL_OR_KEYWORD, annotation=py_type)
            )
        else:
            sig_params.append(
                InspectParam(
                    param.name,
                    InspectParam.POSITIONAL_OR_KEYWORD,
                    default=param.default,
                    annotation=py_type,
                )
            )

    # Create the actual async handler
    async def mcp_handler(*args, **kwargs) -> dict:
        # Merge positional args into kwargs using signature order
        for i, param in enumerate(tool.params):
            if i < len(args):
                kwargs[param.name] = args[i]

        # Parse parameters
        parsed = {}
        for param in tool.params:
            value = kwargs.get(param.name, param.default)
            parsed[param.name] = _parse_param_value(param, value)

        # Get service
        service = create_service(tool)
        if service is None and tool.service:
            missing = ", ".join(tool.service.required_env)
            return {"error": f"Missing configuration: {missing}"}

        # Custom handler?
        if tool.custom_handler:
            result = await tool.custom_handler(service, **parsed)
        else:
            # Call service method
            method = getattr(service, tool.service.method)
            skip_cache = parsed.pop("no_cache", False)
            result = await method(**parsed, skip_cache=skip_cache)

        return result.to_dict()

    # Apply signature and annotations
    mcp_handler.__signature__ = Signature(sig_params, return_annotation=dict)
    mcp_handler.__name__ = tool.mcp_tool_name
    mcp_handler.__doc__ = tool.description

    # Build annotations dict for Pydantic/FastMCP
    annotations = {}
    for param in tool.params:
        annotations[param.name] = _param_to_python_type(param)
    annotations["return"] = dict
    mcp_handler.__annotations__ = annotations

    return mcp_handler


def register_mcp_tool(mcp, tool: ToolDefinition) -> None:
    """Register a single tool as MCP tool."""
    if not tool.mcp_enabled:
        return

    handler = _create_mcp_handler(tool)
    mcp.tool()(handler)


def register_all_mcp_tools(mcp, tools: list[ToolDefinition]) -> None:
    """Register all tools as MCP tools."""
    for tool in tools:
        register_mcp_tool(mcp, tool)


# =============================================================================
# CLI Factory
# =============================================================================


def create_cli_group(app: App, group_name: str, help_text: str) -> App:
    """Create or get a CLI group."""
    # Check if group already exists
    for cmd in app._commands:
        if hasattr(cmd, "name") and cmd.name == group_name:
            return cmd

    group_app = App(name=group_name, help=help_text)
    return group_app


def create_cli_command_func(tool: ToolDefinition):
    """Create a CLI command function for a tool."""

    def command(
        json_output: Annotated[bool, Parameter(name=["-j", "--json"])] = False,
        output: Annotated[Path | None, Parameter(name=["-o", "--output"])] = None,
        **kwargs,
    ) -> None:
        """Execute the tool command."""

        async def _run() -> Any:
            # Parse parameters
            parsed = {}
            for param in tool.params:
                value = kwargs.get(param.name, param.default)
                parsed[param.name] = _parse_param_value(param, value)

            # Get service
            service = create_service(tool)
            if service is None and tool.service:
                missing = ", ".join(tool.service.required_env)
                print(f"Error: Missing configuration - {missing}", file=sys.stderr)
                sys.exit(1)

            # Call service
            if tool.custom_handler:
                result = await tool.custom_handler(service, **parsed)
            else:
                method = getattr(service, tool.service.method)
                skip_cache = parsed.pop("no_cache", False)
                result = await method(**parsed, skip_cache=skip_cache)

            return result

        result = asyncio.run(_run())
        data = result.to_dict()

        if json_output or output:
            # JSON output
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            if output:
                output.write_text(json_str, encoding="utf-8")
            else:
                print(json_str)
        else:
            # Rich output
            if tool.custom_renderer:
                tool.custom_renderer(result)
            elif tool.output:
                render(tool.output, data)
            else:
                # Fallback: print dict
                print(json.dumps(data, indent=2))

    # Set metadata
    command.__name__ = tool.cli_command_name
    command.__doc__ = tool.description

    return command


def _build_cli_annotations(tool: ToolDefinition) -> dict[str, Any]:
    """Build Cyclopts-compatible annotations for tool parameters."""
    annotations = {}

    for param in tool.params:
        # Build CLI names
        cli_names = []
        if param.cli_short:
            cli_names.append(param.cli_short)
        cli_names.append(param.cli_name or f"--{param.name.replace('_', '-')}")

        # Build Parameter with proper settings
        py_type = param.to_cli_type()

        # Create Annotated type with Cyclopts Parameter
        if param.required:
            annotations[param.name] = Annotated[py_type, Parameter(name=cli_names, help=param.description)]
        else:
            annotations[param.name] = Annotated[py_type, Parameter(name=cli_names, help=param.description)]

    # Add standard output params
    annotations["json_output"] = Annotated[bool, Parameter(name=["-j", "--json"])]
    annotations["output_file"] = Annotated[Path | None, Parameter(name=["-o", "--output"])]
    annotations["return"] = None

    return annotations


def _build_cli_signature(tool: ToolDefinition) -> Signature:
    """Build function signature for CLI command."""
    params = []

    for param in tool.params:
        py_type = param.to_cli_type()
        if param.required:
            params.append(InspectParam(param.name, InspectParam.POSITIONAL_OR_KEYWORD, annotation=py_type))
        else:
            params.append(InspectParam(param.name, InspectParam.POSITIONAL_OR_KEYWORD, default=param.default, annotation=py_type))

    # Add standard output params
    params.append(InspectParam("json_output", InspectParam.POSITIONAL_OR_KEYWORD, default=False, annotation=bool))
    params.append(InspectParam("output_file", InspectParam.POSITIONAL_OR_KEYWORD, default=None, annotation=Path | None))

    return Signature(params, return_annotation=None)


def build_cli_command(tool: ToolDefinition, group_app: App) -> None:
    """
    Build and register a CLI command from tool definition.

    This creates a proper Cyclopts command with typed parameters.
    """
    if not tool.cli_enabled:
        return

    # Create the actual command function
    async def _run_impl(kwargs: dict) -> Any:
        # Parse parameters
        parsed = {}
        for param in tool.params:
            value = kwargs.get(param.name, param.default)
            parsed[param.name] = _parse_param_value(param, value)

        # Get service
        service = create_service(tool)
        if service is None and tool.service:
            missing = ", ".join(tool.service.required_env)
            print(f"Error: Missing configuration - {missing}", file=sys.stderr)
            sys.exit(1)

        # Call service
        if tool.custom_handler:
            result = await tool.custom_handler(service, **parsed)
        else:
            method = getattr(service, tool.service.method)
            skip_cache = parsed.pop("no_cache", False)
            result = await method(**parsed, skip_cache=skip_cache)

        return result

    def command_impl(*args, **kwargs) -> None:
        # Merge positional args into kwargs using signature order
        param_names = [p.name for p in tool.params] + ["json_output", "output_file"]
        for i, arg in enumerate(args):
            if i < len(param_names):
                kwargs[param_names[i]] = arg

        # Extract output options
        json_output = kwargs.pop("json_output", False)
        output_file = kwargs.pop("output_file", None)

        try:
            result = asyncio.run(_run_impl(kwargs))
        except Exception as e:
            # Clean error output instead of full traceback
            error_name = type(e).__name__
            print(f"Error: {error_name} - {e}", file=sys.stderr)
            sys.exit(1)

        data = result.to_dict()

        if json_output or output_file:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            if output_file:
                output_file.write_text(json_str, encoding="utf-8")
            else:
                print(json_str)
        else:
            if tool.custom_renderer:
                tool.custom_renderer(result)
            elif tool.output:
                render(tool.output, data)
            else:
                print(json.dumps(data, indent=2))

    # Apply signature and annotations for Cyclopts
    command_impl.__signature__ = _build_cli_signature(tool)
    command_impl.__annotations__ = _build_cli_annotations(tool)
    command_impl.__name__ = tool.cli_command_name
    command_impl.__doc__ = tool.description

    # Register with group
    group_app.command(name=tool.cli_command_name)(command_impl)


def register_tools_to_cli(
    app: App,
    tools: list[ToolDefinition],
    group_configs: dict[str, dict] | None = None,
) -> dict[str, App]:
    """
    Register multiple tools to CLI, organizing by group.

    Args:
        app: Main CLI app
        tools: List of tool definitions
        group_configs: Optional config per group {name: {alias: str, help: str}}

    Returns:
        Dict of group_name -> group_app for further customization
    """
    group_configs = group_configs or {}
    groups: dict[str, App] = {}

    for tool in tools:
        if not tool.cli_enabled:
            continue

        # Get or create group
        if tool.group not in groups:
            config = group_configs.get(tool.group, {})
            group_app = App(
                name=tool.group,
                help=config.get("help", f"{tool.group.title()} commands"),
            )
            groups[tool.group] = group_app

            # Register group with main app
            alias = config.get("alias")
            if alias:
                app.command(group_app, name=tool.group, alias=alias)
            else:
                app.command(group_app, name=tool.group)

        # Build command in group
        build_cli_command(tool, groups[tool.group])

    return groups
