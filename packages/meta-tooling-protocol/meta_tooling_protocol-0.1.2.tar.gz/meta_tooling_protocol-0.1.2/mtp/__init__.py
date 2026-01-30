"""
MTP - minimal Python runtime for APG.
"""

from .core import (
    BlockingInput,
    BlockingOutput,
    InstanceStatus,
    Traceback,
    TracebackFrame,
    Instance,
    get_instance,
    set_instance,
    clear_instance,
    ensure_instance,
    new_instance,
    close_instance,
    get_global_heap,
    heap_get,
    heap_set,
    heap_delete,
    heap_keys,
    heap_clear,
    heap_release,
    heap_lock,
    heap_try_lock,
    help_doc,
    gendoc,
    mcp_api_doc,
    mtp_doc,
    runtime_doc,
    infra_doc,
    exec_doc,
    OpenApiInfra,
    PythonInfra,
    McpInfra,
    CmdInfra,
    CmdTool,
    CmdToolEntry,
    InfraItem,
    InfraManager,
    MTP_ROOT,
    BaseInfraModel,
    load_tools,
)
from .help import exec_description, tool_descriptions
from .pydantic_adapter import PydanticAdapter


class _ToolsetProxy:
    def __init__(self, toolset_model):
        self._toolset = toolset_model
        self._instance = None

    def _ensure_instance(self):
        if self._toolset.obj is None:
            return None
        if self._instance is None:
            self._instance = self._toolset.obj()
        return self._instance

    def __getattr__(self, name: str):
        tool = self._toolset.tools.get(name)
        if tool is None:
            raise AttributeError(name)
        instance = self._ensure_instance()
        if instance is not None and self._toolset.obj is not None:
            return tool.func.__get__(instance, self._toolset.obj)
        return tool.func

    def __dir__(self):
        return sorted(set(self._toolset.tools.keys()))


class _NamespaceProxy:
    def __init__(self, ns_model):
        self._namespace = ns_model

    def __getattr__(self, name: str):
        tool = self._namespace.tools.get(name)
        if tool is not None:
            return tool.func
        toolset = self._namespace.toolsets.get(name)
        if toolset is not None:
            return _ToolsetProxy(toolset)
        raise AttributeError(name)

    def __dir__(self):
        names = set(self._namespace.tools.keys()) | set(self._namespace.toolsets.keys())
        return sorted(names)


class _CmdNamespaceProxy:
    def __init__(self, entries, cmd_infra):
        self._tools = {}
        for entry in entries:
            tool_name = entry.name
            tool_fn = cmd_infra._run_cmd(entry)
            tool_fn.__name__ = str(tool_name)
            self._tools[str(tool_name)] = tool_fn
        self._default = None
        if len(self._tools) == 1:
            self._default = next(iter(self._tools.values()))

    def __call__(self, *args, **kwargs):
        if self._default is None:
            raise TypeError("Cmd namespace is not callable; select a tool.")
        return self._default(*args, **kwargs)

    def __getattr__(self, name: str):
        tool = self._tools.get(name)
        if tool is None:
            raise AttributeError(name)
        return tool

    def __dir__(self):
        return sorted(self._tools.keys())


class _McpProxy:
    def __init__(self, entry, call_tool_sync):
        self._entry = entry
        self._call_tool_sync = call_tool_sync

    def __call__(self, tool: str, arguments: dict | None = None):
        return self._call_tool_sync(self._entry, tool, arguments or {})

    def __getattr__(self, name: str):
        def _tool(**kwargs):
            return self._call_tool_sync(self._entry, name, kwargs)
        _tool.__name__ = name
        return _tool


class _InfraProxy:
    """Proxy for mtp.infra that supports dynamic tool imports."""

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        from types import ModuleType
        import importlib
        import os
        import sys
        from pathlib import Path

        from .core.registry import load_infra, MTP_ROOT
        from .core.python_tools import load_tools, name_module
        from .core.infra import cmd as cmd_infra
        from .core.docgen import registry as doc_registry
        from .core.mcp_client import call_tool_sync

        infra_path = os.getenv("MTP_INFRA") or os.getenv("MTP_INFRA_PATH")
        infra_file = Path(infra_path) if infra_path else None
        infra_manager = load_infra(infra_file) if infra_file else load_infra()
        cmd_entries = infra_manager.cmd_entries()

        # Check cmd tools
        cmd_namespace_entries = [entry for entry in cmd_entries if entry.namespace == name]
        if cmd_namespace_entries:
            return _CmdNamespaceProxy(cmd_namespace_entries, cmd_infra)

        for entry in cmd_entries:
            if entry.name == name:
                tool_fn = cmd_infra._run_cmd(entry)
                tool_fn.__name__ = entry.name
                return tool_fn

        # Check python tools
        for entry in infra_manager.python:
            if entry.name != name:
                continue
            load_tools(infra_manager)
            module_name = entry.module or name_module(entry.name)
            module = sys.modules.get(module_name)
            ns_name = getattr(module, "__namespace__", entry.name) if module else entry.name
            ns_model = doc_registry.get_namespace(ns_name)
            if ns_model:
                return _NamespaceProxy(ns_model)
            if isinstance(module, ModuleType):
                return module

        # Check MCP tools
        for entry in infra_manager.mcps:
            if entry.name == name:
                return _McpProxy(entry, call_tool_sync)

        # Check SDK tools
        for entry in infra_manager.sdks:
            if entry.name == name:
                sdk_root = (infra_file.parent / "sdks") if infra_file else (MTP_ROOT / "sdks")
                sdk_path = str(sdk_root)
                if sdk_path not in sys.path:
                    sys.path.insert(0, sdk_path)
                module = importlib.import_module(entry.name)
                return module

        raise AttributeError(f"Tool '{name}' not found in mtp.infra")

    def __dir__(self):
        import os
        from pathlib import Path
        from .core.registry import load_infra

        infra_path = os.getenv("MTP_INFRA") or os.getenv("MTP_INFRA_PATH")
        infra_manager = load_infra(Path(infra_path)) if infra_path else load_infra()
        infra_names = {entry.name for entry in infra_manager.python + infra_manager.mcps + infra_manager.sdks}
        for entry in infra_manager.cmd_entries():
            infra_names.add(entry.namespace)
        return sorted(infra_names)


# Create infra proxy for dynamic tool imports
infra = _InfraProxy()

# Register infra as a submodule so "from mtp.infra import gogo" works
import sys
sys.modules['mtp.infra'] = infra

try:
    from .langchain import LangchainAdapter
except Exception:  # optional dependency
    LangchainAdapter = None  # type: ignore

try:
    from .api import APIAdapter
except Exception:  # optional dependency
    APIAdapter = None  # type: ignore

try:
    from .mcp_server import MCPAdapter
except Exception:  # optional dependency
    MCPAdapter = None  # type: ignore

__all__ = [
    "BlockingInput",
    "BlockingOutput",
    "InstanceStatus",
    "Traceback",
    "TracebackFrame",
    "Instance",
    "get_instance",
    "set_instance",
    "clear_instance",
    "ensure_instance",
    "new_instance",
    "close_instance",
    "get_global_heap",
    "heap_get",
    "heap_set",
    "heap_delete",
    "heap_keys",
    "heap_clear",
    "heap_release",
    "heap_lock",
    "heap_try_lock",
    "help_doc",
    "gendoc",
    "mcp_api_doc",
    "mtp_doc",
    "runtime_doc",
    "infra_doc",
    "exec_doc",
    "OpenApiInfra",
    "PythonInfra",
    "McpInfra",
    "CmdInfra",
    "CmdTool",
    "CmdToolEntry",
    "InfraItem",
    "InfraManager",
    "BaseInfraModel",
    "MTP_ROOT",
    "load_tools",
    "infra",
    "exec_description",
    "tool_descriptions",
    "PydanticAdapter",
    "LangchainAdapter",
    "MCPAdapter",
    "APIAdapter",
]
