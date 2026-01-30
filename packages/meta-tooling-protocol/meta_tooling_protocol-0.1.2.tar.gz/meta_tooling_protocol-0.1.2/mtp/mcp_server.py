"""
MCP server adapter for MTP.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Optional

from .core.docgen import DocModel, iter_registered_tools
from .core.mcp_client import call_tool, list_tools_sync
from .core.registry import load_infra
from .core.io import BlockingOutput
from .core.runtime import Instance, ensure_instance
from .help import tool_descriptions

__all__ = ["MCPAdapter"]


class MCPAdapter:
    """Expose MTP as MCP stdio or HTTP servers."""

    def __init__(
        self,
        instance: Optional[Instance] = None,
        *,
        name: str = "mtp",
        aggregate: bool = False,
        namespace: str | None = None,
        toolset: str | None = None,
        tool: str | None = None,
        infra_path: Optional[Path] = None,
    ) -> None:
        self._instance = ensure_instance(instance)
        self._name = name
        self._aggregate = aggregate
        self._namespace = namespace
        self._toolset = toolset
        self._tool = tool
        self._infra_path = infra_path

    def server_http(self, *, path: str = ""):
        fastmcp = self._resolve_fastmcp()
        try:
            server = fastmcp(self._name)
        except TypeError:
            server = fastmcp()
        self._register_tools(server)
        return server

    def server_stdio(self, *, path: str = ""):
        fastmcp = self._resolve_fastmcp()
        try:
            server = fastmcp(self._name)
        except TypeError:
            server = fastmcp()
        self._register_tools(server)
        return server

    def serve(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8000,
        path: str = "",
    ) -> None:
        self.serve_http(host=host, port=port, path=path)

    def serve_http(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8000,
        path: str = "",
    ) -> None:
        server = self.server_http(path=path)
        try:
            server.run(transport="http", host=host, port=port, path=path)
        except TypeError:
            server.run(host=host, port=port)
        except AttributeError as exc:
            raise RuntimeError("MCP server does not support run()") from exc

    def serve_stdio(self) -> None:
        server = self.server_stdio()
        try:
            server.run()
        except TypeError:
            server.run(transport="stdio")
        except AttributeError as exc:
            raise RuntimeError("MCP server does not support run()") from exc

    def _register_tools(self, server) -> None:
        try:
            tool = server.tool
        except AttributeError as exc:
            raise RuntimeError("FastMCP server does not support tool registration") from exc
        descriptions = tool_descriptions()
        registered: set[str] = set()

        def python_exec(code: str, notebook_path: Optional[str] = None) -> BlockingOutput:
            active = ensure_instance(self._instance)
            self._instance = active
            if notebook_path:
                active.set_notebook_path(notebook_path)
            return active.exec(code=code)

        tool(name="python_exec", description=descriptions["python_exec"])(python_exec)
        registered.add("python_exec")
        if self._aggregate:
            self._register_aggregate_tools(server, registered)

    @staticmethod
    def _qualified_tool_name(namespace: str, toolset: Optional[str], name: str) -> str:
        if toolset:
            return f"{namespace}.{toolset}.{name}"
        return f"{namespace}.{name}"

    def _register_aggregate_tools(self, server, registered: set[str]) -> None:
        tool = server.tool
        toolset_instances: dict[type, object] = {}
        infra_registry = load_infra(self._infra_path)
        for entry in iter_registered_tools(infra=infra_registry):
            if not self._match(entry.namespace, entry.toolset, entry.name):
                continue
            tool_name = self._qualified_tool_name(entry.namespace, entry.toolset, entry.name)
            if tool_name in registered:
                continue
            func = entry.func
            if entry.toolset:
                if entry.toolset_obj is None:
                    raise RuntimeError(f"Toolset {entry.namespace}.{entry.toolset} has no class to instantiate")
                instance = toolset_instances.get(entry.toolset_obj)
                if instance is None:
                    try:
                        instance = entry.toolset_obj()
                    except Exception as exc:
                        raise RuntimeError(
                            f"Failed to instantiate toolset {entry.namespace}.{entry.toolset}: {exc}"
                        ) from exc
                    toolset_instances[entry.toolset_obj] = instance
                func = entry.func.__get__(instance, entry.toolset_obj)
            description = entry.docmodel.description
            tool(name=tool_name, description=description)(func)
            registered.add(tool_name)
        self._register_mcp_tools(server, registered)

    def _match(self, namespace: str, toolset: Optional[str], name: str) -> bool:
        if self._namespace and namespace != self._namespace:
            return False
        if self._toolset is not None and toolset != self._toolset:
            return False
        if self._tool is not None and name != self._tool:
            return False
        return True

    def _register_mcp_tools(self, server, registered: set[str]) -> None:
        tool = server.tool
        registry = load_infra(self._infra_path)

        for entry in registry.mcps:
            try:
                tools = list_tools_sync(entry)
            except Exception:
                continue
            for tool_info in tools:
                if not tool_info.name:
                    continue
                if not self._match(entry.name, None, tool_info.name):
                    continue
                tool_name = self._qualified_tool_name(entry.name, None, tool_info.name)
                if tool_name in registered:
                    continue

                async def run(
                    _entry=entry,
                    _tool=tool_info.name,
                    **kwargs: Any,
                ) -> Any:
                    return await call_tool(_entry, _tool, kwargs)

                desc = tool_info.description or f"MCP proxy: {entry.name}.{tool_info.name}"
                sig, annotations = self._proxy_signature(tool_info.input_schema)
                run.__signature__ = sig
                run.__annotations__ = annotations
                docmodel = DocModel(description=desc, signature=f"def {tool_info.name}{sig}")
                run.__docmodel__ = docmodel

                tool(name=tool_name, description=desc)(run)
                registered.add(tool_name)

    @staticmethod
    def _proxy_signature(schema: dict[str, Any] | None) -> tuple[inspect.Signature, dict[str, Any]]:
        if not schema or schema.get("type") != "object":
            return inspect.Signature(), {}
        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        params: list[inspect.Parameter] = []
        annotations: dict[str, Any] = {}
        for name in props.keys():
            default = inspect.Parameter.empty if name in required else None
            params.append(
                inspect.Parameter(
                    name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    default=default,
                    annotation=Any,
                )
            )
            annotations[name] = Any
        return inspect.Signature(params), annotations

    @staticmethod
    def _resolve_fastmcp():
        try:
            from fastmcp import FastMCP  # type: ignore
            return FastMCP
        except Exception:
            try:
                from mcp.server.fastapi import FastMCP  # type: ignore
                return FastMCP
            except Exception as exc:
                raise ImportError("fastmcp is required for MCPAdapter") from exc
