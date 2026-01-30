"""
MCP client helpers for stdio and streamable-http transports.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .registry import McpInfra

__all__ = [
    "list_tools_sync",
    "call_tool",
    "call_tool_sync",
    "ToolInfo",
    "ToolCallResult",
]


class MCPClientError(RuntimeError):
    pass


class ToolInfo(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, from_attributes=True)

    name: str | None = None
    description: str | None = None
    input_schema: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("inputSchema", "input_schema"),
        serialization_alias="inputSchema",
    )


class ToolList(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    tools: list[ToolInfo] = Field(default_factory=list)


class ToolCallResult(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, from_attributes=True)

    content: list[dict[str, Any]] = Field(default_factory=list)
    is_error: bool | None = Field(default=None, validation_alias=AliasChoices("isError", "is_error"))


def _normalize_transport(transport: str) -> str:
    value = transport.lower().replace("_", "-")
    if value in {"streamhttp", "stream-http", "streamable-http", "http"}:
        return "streamable-http"
    if value == "stdio":
        return "stdio"
    raise MCPClientError(f"Unsupported MCP transport: {transport}")


def _resolve_mcp_objects():
    try:
        from mcp import ClientSession  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("mcp client is required. Install with: pip install \"mtp[mcp]\"") from exc

    try:
        from mcp import StdioServerParameters  # type: ignore
    except Exception:
        try:
            from mcp.client.stdio import StdioServerParameters  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ImportError("mcp stdio support is required. Install with: pip install \"mtp[mcp]\"") from exc

    return ClientSession, StdioServerParameters


def _resolve_stdio_client():
    try:
        from mcp.client.stdio import stdio_client  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("mcp stdio client is required. Install with: pip install \"mtp[mcp]\"") from exc
    return stdio_client


def _resolve_streamable_http_client():
    candidates = [
        ("mcp.client.streamable_http", "streamable_http_client"),
        ("mcp.client.streamable_http", "stream_http_client"),
        ("mcp.client.stream_http", "stream_http_client"),
    ]
    for module_name, func_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        func = getattr(module, func_name, None)
        if func is not None:
            return func
    raise ImportError("mcp streamable-http client is required. Install with: pip install \"mtp[mcp]\"")


def _build_stdio_params(entry: McpInfra, StdioServerParameters):
    if not entry.command:
        raise MCPClientError("MCP stdio server missing command.")
    params = {"command": entry.command, "args": entry.args or []}
    if entry.env:
        params["env"] = entry.env
    allowed = inspect.signature(StdioServerParameters).parameters
    params = {key: value for key, value in params.items() if key in allowed}
    return StdioServerParameters(**params)


def _extract_tools(result: Any) -> list[ToolInfo]:
    try:
        return ToolList.model_validate(result).tools
    except Exception:
        return ToolList.model_validate({"tools": result}).tools


def _dump_content_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    for attr in ("model_dump", "dict"):
        method = getattr(item, attr, None)
        if callable(method):
            return method()
    return {"type": getattr(item, "type", "unknown"), "text": getattr(item, "text", str(item))}


def _call_result(result: Any) -> ToolCallResult:
    if isinstance(result, ToolCallResult):
        return result
    try:
        return ToolCallResult.model_validate(result)
    except Exception:
        pass
    raw_content = getattr(result, "content", None)
    content = [_dump_content_item(item) for item in raw_content] if isinstance(raw_content, list) else []
    return ToolCallResult.model_validate(
        {
            "content": content,
            "isError": getattr(result, "isError", None),
            "is_error": getattr(result, "is_error", None),
        }
    )


def _streamable_kwargs(client: Any, headers: dict[str, Any] | None) -> dict[str, Any]:
    if not headers:
        return {}
    try:
        sig = inspect.signature(client)
    except (TypeError, ValueError):
        return {"headers": headers}
    if "headers" in sig.parameters:
        return {"headers": headers}
    if "extra_headers" in sig.parameters:
        return {"extra_headers": headers}
    return {}


async def _with_session(entry: McpInfra, call):
    ClientSession, StdioServerParameters = _resolve_mcp_objects()
    transport = _normalize_transport(entry.transport)

    async def run(client_ctx):
        async with client_ctx as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await call(session)

    if transport == "stdio":
        stdio_client = _resolve_stdio_client()
        params = _build_stdio_params(entry, StdioServerParameters)
        return await run(stdio_client(params))
    if not entry.url:
        raise MCPClientError("MCP streamable-http server missing url.")
    streamable_http_client = _resolve_streamable_http_client()
    kwargs = _streamable_kwargs(streamable_http_client, entry.headers)
    if kwargs:
        try:
            return await run(streamable_http_client(entry.url, **kwargs))
        except TypeError:
            return await run(streamable_http_client(entry.url))
    return await run(streamable_http_client(entry.url))


async def _list_tools_async(entry: McpInfra) -> list[ToolInfo]:
    result = await _with_session(entry, lambda session: session.list_tools())
    tools = _extract_tools(result)
    if not tools:
        raise MCPClientError("Unexpected MCP list_tools response.")
    return tools


def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise MCPClientError("Cannot run MCP client in an active event loop.")


def list_tools_sync(entry: McpInfra) -> list[ToolInfo]:
    return _run_sync(_list_tools_async(entry))


async def _call_tool_async(
    entry: McpInfra,
    tool_name: str,
    arguments: dict[str, Any],
) -> ToolCallResult:
    result = await _with_session(entry, lambda session: session.call_tool(tool_name, arguments))
    return _call_result(result)


async def call_tool(
    entry: McpInfra,
    tool_name: str,
    arguments: dict[str, Any],
) -> ToolCallResult:
    return await _call_tool_async(entry, tool_name, arguments)


def call_tool_sync(
    entry: McpInfra,
    tool_name: str,
    arguments: dict[str, Any],
) -> ToolCallResult:
    return _run_sync(_call_tool_async(entry, tool_name, arguments))
