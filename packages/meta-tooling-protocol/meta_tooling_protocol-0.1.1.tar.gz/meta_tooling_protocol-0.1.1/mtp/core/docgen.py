"""Unified doc generation for OpenAPI, MCP, and manual doc registries."""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from .registry import InfraManager, OpenApiInfra, load_infra
from .python_tools import load_tools, name_module
from .mcp_client import list_tools_sync

__all__ = [
    "DocModel",
    "ToolModel",
    "ToolsetModel",
    "NamespaceModel",
    "Registry",
    "registry",
    "RegisteredTool",
    "render_sections",
    "help_doc",
    "gendoc",
    "namespace",
    "tool",
    "toolset",
    "register_namespace",
    "register_toolset",
    "register_tool",
    "register_namespace_tool",
    "iter_registered_tools",
    "DocGenerator",
    "register_generator",
    "get_generator",
    "list_generators",
    "list_namespaces",
    "list_toolsets",
    "list_tools",
    "docs",
]



def _md_section(level: int, title: str, *content: str) -> str:
    lines = [f"{'#' * level} {title}", ""]
    lines.extend(content)
    return "\n".join(lines)


def _md_code(code: str, lang: str = "python") -> str:
    return f"```{lang}\n{code}\n```"


def render_sections(sections: list[tuple[str, str]]) -> str:
    rendered: list[str] = []
    for title, content in sections:
        if not content:
            continue
        rendered.append(_md_section(1, title, content))
    return "\n\n".join(rendered)


class DocModel(BaseModel):
    description: str = ""
    signature: str = ""

    def get_short_description(self) -> str:
        return self.description.split("\n\n####")[0].strip()

    @classmethod
    def from_docstring(cls, docstring: str, fallback: str = "") -> "DocModel":
        from docstring_parser import parse

        if not docstring:
            return cls(description=fallback)

        parsed = parse(docstring)
        parts = [p for p in [parsed.short_description, parsed.long_description] if p]
        return cls(description="\n\n".join(parts) or fallback)

    @classmethod
    def from_function(cls, func: Callable[..., Any]) -> "DocModel":
        from docstring_parser import parse

        if not func.__doc__:
            return cls(description=func.__name__, signature=f"def {func.__name__}{inspect.signature(func)}")

        parsed = parse(func.__doc__)
        parts = [p for p in [parsed.short_description, parsed.long_description] if p]

        for meta in parsed.meta:
            if type(meta).__name__ == "DocstringExample" and meta.description:
                parts.append(f"#### Example\n\n{meta.description}")

        description = "\n\n".join(parts) if parts else func.__name__
        signature = f"def {func.__name__}{inspect.signature(func)}"
        return cls(description=description, signature=signature)

    def _split_sections(self) -> tuple[str, list[tuple[str, str]]]:
        description = self.description or ""
        if "\n\n#### " not in description:
            return description.strip(), []
        parts = description.split("\n\n#### ")
        short_desc = parts[0].strip()
        sections: list[tuple[str, str]] = []
        for section in parts[1:]:
            title, _, body = section.partition("\n\n")
            title = title.strip() or "Details"
            sections.append((title, body.strip()))
        return short_desc, sections

    def man(self, tool_name: str = "") -> str:
        short_desc, sections = self._split_sections()

        parts = []
        if tool_name:
            parts.append(_md_section(1, tool_name, short_desc))
        else:
            parts.append(short_desc)

        if self.signature:
            parts.append(_md_section(2, "Signature", _md_code(self.signature)))

        for title, content in sections:
            if not content:
                continue
            parts.append(_md_section(2, title, content))

        return "\n\n".join(parts)


class ToolModel(BaseModel):
    name: str
    func: Any = Field(exclude=True)
    docmodel: DocModel = Field(default_factory=DocModel)

    def man(self) -> str:
        return self.docmodel.man(self.name)


class ToolsetModel(BaseModel):
    name: str
    obj: type | None = Field(default=None, exclude=True)
    tools: dict[str, ToolModel] = Field(default_factory=dict)
    docmodel: DocModel = Field(default_factory=DocModel)

    def man(self) -> str:
        sections = [_md_section(1, self.name, self.docmodel.description), _md_section(2, "tool")]
        for tool in self.tools.values():
            content = [tool.docmodel.get_short_description()]
            if tool.docmodel.signature:
                content.extend(["", _md_code(tool.docmodel.signature)])
            sections.append(_md_section(3, tool.name, *content))
        return "\n\n".join(sections)


class NamespaceModel(BaseModel):
    name: str
    obj: Any = Field(default=None, exclude=True)
    toolsets: dict[str, ToolsetModel] = Field(default_factory=dict)
    tools: dict[str, ToolModel] = Field(default_factory=dict)
    docmodel: DocModel = Field(default_factory=DocModel)

    def man(self) -> str:
        sections = [_md_section(1, self.name, self.docmodel.description)]

        sub_namespaces = [
            n
            for n in registry.list_namespaces()
            if n.startswith(f"{self.name}.") and n.count(".") == self.name.count(".") + 1
        ]
        if sub_namespaces:
            sections.append(_md_section(2, "namespace"))
            for sub_ns in sub_namespaces:
                ns_model = registry.get_namespace(sub_ns)
                sections.append(_md_section(3, sub_ns.split(".")[-1], ns_model.docmodel.description))

        if self.toolsets:
            sections.append(_md_section(2, "toolset"))
            for ts in self.toolsets.values():
                sections.append(_md_section(3, ts.name, ts.docmodel.description))

        if self.tools:
            sections.append(_md_section(2, "tool"))
            for t in self.tools.values():
                sections.append(_md_section(3, t.name, t.docmodel.description))

        return "\n\n".join(sections)


class Registry:
    def __init__(self) -> None:
        self._namespaces: dict[str, NamespaceModel] = {}

    def register_namespace(self, name: str, obj: Any) -> None:
        if name in self._namespaces:
            return
        docmodel = DocModel.from_docstring(obj.__doc__ if obj else "", name)
        self._namespaces[name] = NamespaceModel(name=name, obj=obj, docmodel=docmodel)

    def register_toolset(self, namespace_name: str, name: str, obj: type) -> None:
        self.register_namespace(namespace_name, None)
        if name in self._namespaces[namespace_name].toolsets:
            return
        docmodel = DocModel.from_docstring(obj.__doc__ if obj else "", name)
        self._namespaces[namespace_name].toolsets[name] = ToolsetModel(
            name=name, obj=obj, docmodel=docmodel
        )

    def register_tool(self, namespace_name: str, toolset_name: str, name: str, func: Any) -> None:
        self.register_namespace(namespace_name, None)
        if toolset_name not in self._namespaces[namespace_name].toolsets:
            self.register_toolset(namespace_name, toolset_name, None)
        docmodel = getattr(func, "__docmodel__", DocModel(description=name))
        self._namespaces[namespace_name].toolsets[toolset_name].tools[name] = ToolModel(
            name=name, func=func, docmodel=docmodel
        )

    def register_namespace_tool(self, namespace_name: str, name: str, func: Any) -> None:
        self.register_namespace(namespace_name, None)
        docmodel = getattr(func, "__docmodel__", DocModel(description=name))
        self._namespaces[namespace_name].tools[name] = ToolModel(name=name, func=func, docmodel=docmodel)

    def get_namespace(self, name: str) -> NamespaceModel | None:
        return self._namespaces.get(name)

    def get_toolset(self, namespace_name: str, toolset_name: str) -> ToolsetModel | None:
        ns = self._namespaces.get(namespace_name)
        return ns.toolsets.get(toolset_name) if ns else None

    def get_tool(self, namespace_name: str, toolset_name: str, tool_name: str) -> ToolModel | None:
        ts = self.get_toolset(namespace_name, toolset_name)
        return ts.tools.get(tool_name) if ts else None

    def list_namespaces(self) -> list[str]:
        return list(self._namespaces.keys())

    def list_toolsets(self, namespace_name: str) -> list[str]:
        return list(self._namespaces[namespace_name].toolsets.keys())

    def list_tools(self, namespace_name: str, toolset_name: str) -> list[str]:
        return list(self._namespaces[namespace_name].toolsets[toolset_name].tools.keys())


registry = Registry()


def _is_manual_namespace(name: str) -> bool:
    return registry.get_namespace(name) is not None


def _is_mcp_namespace(name: str, infra: InfraManager | None = None) -> bool:
    infra = infra or load_infra()
    return name in mcp_list_namespaces(infra)


def _load_infra(infra: InfraManager | None = None) -> None:
    load_tools(infra)
    from .infra import cmd as cmd_infra

    cmd_infra.load_cmds(infra)


def _all_namespaces(infra: InfraManager | None = None) -> list[str]:
    infra = infra or load_infra()
    _load_infra(infra)
    manual_namespaces = registry.list_namespaces()
    infra_namespaces = fern_list_namespaces(infra)
    mcp_namespaces = mcp_list_namespaces(infra)
    return sorted(set(manual_namespaces + infra_namespaces + mcp_namespaces))


def _split_doc_path(
    path: str,
    infra: InfraManager | None = None,
) -> tuple[str | None, str | None, str | None]:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return None, None, None
    namespaces = _all_namespaces(infra=infra)
    for idx in range(len(parts), 0, -1):
        candidate = ".".join(parts[:idx])
        if candidate in namespaces:
            remainder = parts[idx:]
            toolset = remainder[0] if len(remainder) > 0 else None
            tool = remainder[1] if len(remainder) > 1 else None
            return candidate, toolset, tool
    namespace = parts[0]
    toolset = parts[1] if len(parts) > 1 else None
    tool = parts[2] if len(parts) > 2 else None
    return namespace, toolset, tool


def help_doc(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra: InfraManager | None = None,
) -> str:
    infra = infra or load_infra()
    _load_infra(infra)
    if toolset is None and tool is None and isinstance(namespace, str) and "." in namespace:
        namespace, toolset, tool = _split_doc_path(namespace, infra=infra)
    if namespace is None:
        if tool is None and toolset is not None:
            tool = toolset
            toolset = None
        return combined_docs(infra, tool=tool)
    if _is_manual_namespace(namespace):
        return manual_docs(namespace, toolset, tool)
    if _is_mcp_namespace(namespace, infra):
        return mcp_docs(namespace, toolset, tool, infra=infra)
    if namespace not in fern_list_namespaces(infra):
        return f"Unknown namespace: {namespace}"
    return fern_docs(namespace, toolset, tool, infra=infra)


def gendoc(infra: InfraManager | None = None) -> str:
    infra = infra or load_infra()
    return docs(generator="openapi", infra=infra)


def register_namespace(name: str, obj: Any = None) -> None:
    """Register a namespace without using decorators.
    
    Args:
        name: Namespace name
        obj: Optional namespace object (module or class)
    """
    registry.register_namespace(name, obj)


def register_toolset(namespace_name: str, name: str, obj: type | None = None) -> None:
    """Register a toolset without using decorators.
    
    Args:
        namespace_name: Parent namespace name
        name: Toolset name
        obj: Optional toolset class
    """
    registry.register_toolset(namespace_name, name, obj)


def register_tool(
    namespace_name: str, toolset_name: str, name: str, func: Callable[..., Any]
) -> None:
    """Register a tool without using decorators.
    
    Args:
        namespace_name: Parent namespace name
        toolset_name: Parent toolset name
        name: Tool name
        func: Tool function
    """
    registry.register_tool(namespace_name, toolset_name, name, func)


def register_namespace_tool(namespace_name: str, name: str, func: Callable[..., Any]) -> None:
    """Register a tool at namespace level without using decorators.
    
    Args:
        namespace_name: Parent namespace name
        name: Tool name
        func: Tool function
    """
    registry.register_namespace_tool(namespace_name, name, func)


class RegisteredTool(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    namespace: str
    toolset: str | None
    name: str
    func: Any
    docmodel: DocModel
    toolset_obj: type | None = None


class InfraToolDoc(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    signature: str | None = None
    toolset: str | None = None


InfraEntry = tuple[str, str, str | None, list[InfraToolDoc]]


def iter_registered_tools(infra: InfraManager | None = None):
    infra = infra or load_infra()
    _load_infra(infra)
    for ns_name in registry.list_namespaces():
        ns = registry.get_namespace(ns_name)
        if ns is None:
            continue
        for tool in ns.tools.values():
            yield RegisteredTool(
                namespace=ns_name,
                toolset=None,
                name=tool.name,
                func=tool.func,
                docmodel=tool.docmodel,
                toolset_obj=None,
            )
        for ts_name, ts in ns.toolsets.items():
            for tool in ts.tools.values():
                yield RegisteredTool(
                    namespace=ns_name,
                    toolset=ts_name,
                    name=tool.name,
                    func=tool.func,
                    docmodel=tool.docmodel,
                    toolset_obj=ts.obj,
                )



def namespace(name: str | None = None):
    import inspect as _inspect
    import sys as _sys

    frame = _inspect.currentframe().f_back
    caller_module = frame.f_globals["__name__"]
    name = name or caller_module.split(".")[-1]

    parent_ns = None
    if "." in caller_module:
        parent_module = _sys.modules.get(caller_module.rsplit(".", 1)[0])
        if parent_module:
            parent_ns = getattr(parent_module, "__namespace__", None)

    full_name = f"{parent_ns}.{name}" if parent_ns else name
    current_module = _sys.modules[caller_module]
    current_module.__namespace__ = full_name
    registry.register_namespace(full_name, current_module)
    current_module.man = lambda: registry.get_namespace(full_name).man()

    return full_name


def tool(name: str | None = None, desc: str | None = None):
    from functools import wraps
    from typing import cast

    def wrap(func: Callable[..., Any]):
        tool_name = name or func.__name__
        doc_model = DocModel(description=desc) if desc else DocModel.from_function(func)

        @wraps(func)
        async def async_wrapped(*a, **k):
            return await func(*a, **k)

        @wraps(func)
        def sync_wrapped(*a, **k):
            return func(*a, **k)

        wrapped = async_wrapped if inspect.iscoroutinefunction(func) else sync_wrapped
        wrapped.__tool_name__ = tool_name
        wrapped.__is_tool__ = True
        wrapped.__docmodel__ = doc_model
        wrapped.__doc__ = doc_model.man(tool_name)
        wrapped.man = lambda: doc_model.man(tool_name)

        if "." not in func.__qualname__:
            import sys as _sys

            module = _sys.modules[func.__module__]
            namespace_name = getattr(module, "__namespace__", None)
            if not namespace_name:
                namespace_name = module.__name__
                module.__namespace__ = namespace_name
                registry.register_namespace(namespace_name, module)
                module.man = lambda: registry.get_namespace(namespace_name).man()
            namespace_name = cast(str, namespace_name)
            registry.register_namespace_tool(namespace_name, tool_name, wrapped)

        return wrapped

    return wrap


def toolset(name: str | None = None):
    def wrap(cls: type) -> type:
        tools = [n for n in dir(cls) if not n.startswith("_") and getattr(getattr(cls, n), "__is_tool__", False)]
        toolset_name = name or cls.__name__
        import sys as _sys
        from typing import cast

        module = _sys.modules[cls.__module__]
        ns = getattr(module, "__namespace__", None)
        if not ns:
            ns = module.__name__
            module.__namespace__ = ns
            registry.register_namespace(ns, module)
            module.man = lambda: registry.get_namespace(ns).man()
        ns = cast(str, ns)

        cls.__toolset_name__ = toolset_name
        cls.__namespace__ = ns
        cls.__tools__ = tools
        cls.__docmodel__ = DocModel.from_docstring(cls.__doc__ or "", toolset_name)

        registry.register_toolset(ns, toolset_name, cls)
        for t in tools:
            registry.register_tool(ns, toolset_name, getattr(cls, t).__tool_name__, getattr(cls, t))

        cls.man = classmethod(lambda c: registry.get_toolset(ns, toolset_name).man())
        return cls

    return wrap


def manual_list_namespaces() -> list[str]:
    _load_infra()
    return registry.list_namespaces()


def manual_list_toolsets(namespace_name: str) -> list[str]:
    _load_infra()
    return registry.list_toolsets(namespace_name)


def manual_list_tools(namespace_name: str, toolset_name: str) -> list[str]:
    _load_infra()
    return registry.list_tools(namespace_name, toolset_name)


def manual_docs(
    namespace_name: str | None = None,
    toolset_name: str | None = None,
    tool_name: str | None = None,
) -> str:
    _load_infra()
    if namespace_name and toolset_name and tool_name:
        tool = registry.get_tool(namespace_name, toolset_name, tool_name)
        if tool is None:
            return f"Unknown tool: {namespace_name}.{toolset_name}.{tool_name}"
        return tool.man()
    if namespace_name and toolset_name:
        toolset = registry.get_toolset(namespace_name, toolset_name)
        if toolset is None:
            return f"Unknown toolset: {namespace_name}.{toolset_name}"
        return toolset.man()
    if namespace_name:
        namespace = registry.get_namespace(namespace_name)
        if namespace is None:
            return f"Unknown namespace: {namespace_name}"
        return namespace.man()
    return "\n\n".join(registry.get_namespace(ns).man() for ns in registry.list_namespaces())


def _infer_sdk_type(entry: Any) -> str:
    source = entry.source or ""
    return "grpc" if source.lower().endswith(".proto") else "openapi"


def _append_tool_doc(lines: list[str], tool: ToolModel) -> None:
    lines.append(f"### {tool.name}")
    if tool.docmodel.description:
        lines.append(tool.docmodel.description)
    if tool.docmodel.signature:
        lines.append(_md_code(tool.docmodel.signature))
    lines.append("")


def _append_toolset_docs(lines: list[str], toolset: ToolsetModel) -> None:
    lines.append(f"## {toolset.name}")
    if toolset.docmodel.description:
        lines.append(toolset.docmodel.description)
    lines.append("")
    for tool in sorted(toolset.tools.values(), key=lambda item: item.name):
        _append_tool_doc(lines, tool)


def _tool_filter_match(tool_filter: str, tool: Any) -> bool:
    name = getattr(tool, "name", None)
    toolset = getattr(tool, "toolset", None)
    if name == tool_filter:
        return True
    if toolset and name and tool_filter in {toolset, f"{toolset}.{name}"}:
        return True
    if isinstance(name, str) and "." in name and name.split(".")[-1] == tool_filter:
        return True
    return False


def combined_docs(infra: InfraManager | None = None, tool: str | None = None) -> str:
    infra = infra or load_infra()
    _load_infra(infra)
    lines: list[str] = []

    mtp_ns = registry.get_namespace("mtp")
    if mtp_ns:
        runtime_toolset = mtp_ns.toolsets.get("runtime")
        builtin_tools: list[ToolModel] = []
        if runtime_toolset:
            builtin_tools.extend(runtime_toolset.tools.values())
        builtin_tools.extend(mtp_ns.tools.values())
        if tool is not None:
            builtin_tools = [t for t in builtin_tools if _tool_filter_match(tool, t)]

        if tool is None or builtin_tools:
            lines.append("# mtp")
            if mtp_ns.docmodel.description:
                lines.append(mtp_ns.docmodel.description)
            lines.append("")

            if runtime_toolset:
                lines.append("## runtime")
                if runtime_toolset.docmodel.description:
                    lines.append(runtime_toolset.docmodel.description)
                lines.append("")

            lines.append("## builtin")
            lines.append("")
            if builtin_tools:
                for tool_item in sorted(builtin_tools, key=lambda item: item.name):
                    _append_tool_doc(lines, tool_item)
            elif tool is None:
                lines.append("No builtin tools registered.")
                lines.append("")

    lines.append("# infra")
    lines.append("Registered external tools from infra.yaml.")
    lines.append("")

    entries: list[InfraEntry] = []

    for entry in infra.sdks:
        entry_type = entry.type or _infer_sdk_type(entry)
        desc = f"source: {entry.source}"
        tools: list[InfraToolDoc] = []
        try:
            pkg = importlib.import_module(entry.name)
            for toolset_name, cls in _iter_toolsets(pkg):
                for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue
                    docmodel = _parse_fern_method_doc(method)
                    tools.append(
                        InfraToolDoc(
                            name=method_name,
                            toolset=toolset_name,
                            description=docmodel.description,
                            signature=docmodel.signature,
                        )
                    )
        except Exception:
            tools = []
        if tool is not None:
            tools = [t for t in tools if _tool_filter_match(tool, t)]
            if not tools and entry.name != tool:
                continue
        entries.append((entry.name, entry_type, desc, tools))

    for entry in infra.mcps:
        desc = entry.description or f"transport: {entry.transport}"
        tools: list[InfraToolDoc] = []
        try:
            tool_items = list_tools_sync(entry)
            for tool_item in tool_items:
                if not tool_item.name:
                    continue
                tools.append(
                    InfraToolDoc(
                        name=tool_item.name,
                        toolset=entry.name,
                        description=tool_item.description,
                    )
                )
        except Exception:
            tools = []
        if tool is not None:
            tools = [t for t in tools if _tool_filter_match(tool, t)]
            if not tools and entry.name != tool:
                continue
        entries.append((entry.name, "mcp", desc, tools))

    for entry in infra.python:
        desc = entry.description or f"path: {entry.path}"
        tools: list[InfraToolDoc] = []
        module_name = entry.module or name_module(entry.name)
        module = sys.modules.get(module_name)
        ns_name = getattr(module, "__namespace__", module_name) if module else module_name
        ns_model = registry.get_namespace(ns_name)
        if ns_model:
            for toolset in sorted(ns_model.toolsets.values(), key=lambda item: item.name):
                for tool in sorted(toolset.tools.values(), key=lambda item: item.name):
                    tools.append(
                        InfraToolDoc(
                            name=tool.name,
                            toolset=toolset.name,
                            description=tool.docmodel.description,
                            signature=tool.docmodel.signature,
                        )
                    )
            for tool in sorted(ns_model.tools.values(), key=lambda item: item.name):
                tools.append(
                    InfraToolDoc(
                        name=tool.name,
                        toolset=entry.name,
                        description=tool.docmodel.description,
                        signature=tool.docmodel.signature,
                    )
                )
        if tool is not None:
            tools = [t for t in tools if _tool_filter_match(tool, t)]
            if not tools and entry.name != tool:
                continue
        entries.append((entry.name, "python", desc, tools))

    cmd_groups: dict[str, list[InfraToolDoc]] = {}
    for entry in infra.cmd_entries():
        namespace = entry.namespace or entry.name
        toolset = entry.toolset or namespace
        tool_name = entry.name
        tools = cmd_groups.setdefault(namespace, [])
        tools.append(InfraToolDoc(name=tool_name, toolset=toolset, description=entry.description))
    for namespace, tools in cmd_groups.items():
        if tool is not None and namespace != tool:
            tools = [t for t in tools if _tool_filter_match(tool, t)]
            if not tools:
                continue
        entries.append((namespace, "cmd", None, tools))

    if not entries:
        if tool is None:
            lines.append("No infra tools registered. Run `mtp add ...` first.")
        else:
            lines.append(f"No infra tools matched: {tool}")
        return "\n".join(lines).strip()

    for name, entry_type, desc, tools in sorted(entries, key=lambda item: item[0]):
        lines.append(f"## {name}")
        lines.append(f"type: {entry_type}")
        lines.append(f"import: from mtp import {name}")
        if desc:
            lines.append(desc)
        lines.append("")
        if not tools:
            lines.append("No tools discovered.")
            lines.append("")
            continue
        if any(tool_item.toolset for tool_item in tools):
            toolsets: dict[str, list[InfraToolDoc]] = {}
            for tool_item in tools:
                toolsets.setdefault(tool_item.toolset or "default", []).append(tool_item)
            for toolset_name, tool_items in sorted(toolsets.items()):
                lines.append(f"### {toolset_name}")
                lines.append("")
                for tool_item in sorted(tool_items, key=lambda item: item.name):
                    lines.append(f"#### {tool_item.name}")
                    if tool_item.description:
                        lines.append(tool_item.description)
                    if tool_item.signature:
                        lines.append(_md_code(tool_item.signature))
                    lines.append("")
        else:
            for tool_item in tools:
                lines.append(f"### {tool_item.name}")
                if tool_item.description:
                    lines.append(tool_item.description)
                if tool_item.signature:
                    lines.append(_md_code(tool_item.signature))
                lines.append("")

    return "\n".join(lines).strip()


def _get_mcp_entry(namespace_name: str, infra: InfraManager) -> Any | None:
    for entry in infra.mcps:
        if entry.name == namespace_name:
            return entry
    return None


def mcp_list_namespaces(infra: InfraManager | None = None) -> list[str]:
    infra = infra or load_infra()
    return sorted({entry.name for entry in infra.mcps if entry.name})


def mcp_list_toolsets(namespace_name: str, infra: InfraManager | None = None) -> list[str]:
    return [namespace_name]


def mcp_list_tools(
    namespace_name: str,
    toolset_name: str | None = None,
    infra: InfraManager | None = None,
) -> list[str]:
    infra = infra or load_infra()
    entry = _get_mcp_entry(namespace_name, infra)
    if entry is None:
        return []
    try:
        tools = list_tools_sync(entry)
    except Exception:
        return []
    return [tool.name for tool in tools if tool.name]


def mcp_docs(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra: InfraManager | None = None,
) -> str:
    infra = infra or load_infra()
    if tool is None and toolset is not None:
        tool = toolset
        toolset = None
    entries = infra.mcps
    if namespace:
        entry = _get_mcp_entry(namespace, infra)
        if entry is None:
            return f"Unknown namespace: {namespace}"
        entries = [entry]
    if not entries:
        return "No MCP servers registered. Run `mtp add <name>` first."

    sections: list[str] = []
    for entry in entries:
        sections.append(f"# {entry.name}")
        if entry.description:
            sections.append(entry.description)
        if entry.server or entry.version:
            server_desc = entry.server or "unknown"
            version_desc = entry.version or "unknown"
            sections.append(f"Registry: {server_desc}@{version_desc}")
        sections.append(f"Transport: {entry.transport}")
        sections.append("")
        try:
            tools = list_tools_sync(entry)
        except Exception as exc:
            sections.append(f"Failed to fetch tools: {exc}")
            sections.append("")
            continue
        for tool_item in tools:
            tool_name = tool_item.name
            if not tool_name:
                continue
            if tool and tool_name != tool:
                continue
            sections.append(f"## {tool_name}")
            if tool_item.description:
                sections.append(tool_item.description)
            schema = tool_item.input_schema
            if schema:
                sections.append(_md_section(3, "Input Schema", _md_code(json.dumps(schema, indent=2), lang="json")))
            sections.append("")
        sections.append("")
    return "\n".join(section for section in sections if section is not None)


def _first_line(doc: str | None) -> str:
    if not doc:
        return ""
    return doc.strip().splitlines()[0]


def _safe_signature(func: Any) -> str:
    return str(inspect.signature(func))


def _find_entry_client(pkg: Any) -> Any | None:
    client_mod = importlib.import_module(f"{pkg.__name__}.client")
    for _, cls in inspect.getmembers(client_mod, inspect.isclass):
        if cls.__module__ != client_mod.__name__:
            continue
        if cls.__name__.endswith("Api"):
            return cls
    return None


def _iter_toolsets(pkg: Any) -> list[tuple[str, type]]:
    toolsets: list[tuple[str, type]] = []
    if not getattr(pkg, "__path__", None):
        return toolsets
    for module_info in pkgutil.iter_modules(pkg.__path__):
        if not module_info.ispkg:
            continue
        mod_name = module_info.name
        client_mod_name = f"{pkg.__name__}.{mod_name}.client"
        try:
            client_mod = importlib.import_module(client_mod_name)
        except ModuleNotFoundError:
            # Skip packages that don't expose a client module (e.g. core, errors).
            continue
        for _, cls in inspect.getmembers(client_mod, inspect.isclass):
            if cls.__module__ != client_mod.__name__:
                continue
            if cls.__name__.endswith("Client") and not cls.__name__.startswith("Async"):
                toolsets.append((mod_name, cls))
                break
    return toolsets


def fern_list_namespaces(infra: InfraManager | None = None) -> list[str]:
    infra = infra or load_infra()
    return sorted({entry.name for entry in infra.sdks if entry.name})


def fern_list_toolsets(namespace_name: str, infra: InfraManager | None = None) -> list[str]:
    entry = (infra or load_infra()).get(namespace_name)
    if not isinstance(entry, OpenApiInfra):
        return []
    pkg = importlib.import_module(entry.name)
    return [name for name, _ in _iter_toolsets(pkg)]


def fern_list_tools(namespace_name: str, toolset_name: str, infra: InfraManager | None = None) -> list[str]:
    entry = (infra or load_infra()).get(namespace_name)
    if not isinstance(entry, OpenApiInfra):
        return []
    pkg = importlib.import_module(entry.name)
    for name, cls in _iter_toolsets(pkg):
        if name != toolset_name:
            continue
        return [
            method_name
            for method_name, method in inspect.getmembers(cls, inspect.isfunction)
            if not method_name.startswith("_")
        ]
    return []


def _parse_fern_method_doc(method: Any) -> DocModel:
    """Parse complete docstring from a Fern method using DocModel.

    Returns:
        DocModel with parsed documentation
    """
    docmodel = DocModel.from_function(method)
    if "#### Example" in docmodel.description:
        docmodel.description = docmodel.description.split("\n\n#### Example", 1)[0].strip()
    return docmodel


def fern_docs(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra: InfraManager | None = None,
) -> str:
    infra = infra or load_infra()
    sections: list[str] = []
    namespaces = [namespace] if namespace else fern_list_namespaces(infra)
    for ns in namespaces:
        entry = infra.get(ns)
        if not isinstance(entry, OpenApiInfra):
            continue
        pkg = importlib.import_module(entry.name)
        sections.append(f"# {ns}")
        entry_client = _find_entry_client(pkg)
        if entry_client is not None:
            sig = _safe_signature(entry_client.__init__)
            sections.append(f"Entry client: {entry_client.__name__}{sig}")
        sections.append("")
        for ts_name, ts_cls in _iter_toolsets(pkg):
            if toolset and ts_name != toolset:
                continue
            sections.append(f"## {ts_name}")
            toolset_desc = _first_line(ts_cls.__doc__)
            if not toolset_desc:
                toolset_desc = f"Client: {ts_cls.__name__}{_safe_signature(ts_cls.__init__)}"
            if toolset_desc:
                sections.append(toolset_desc)
                sections.append("")
            for method_name, method in inspect.getmembers(ts_cls, inspect.isfunction):
                if method_name.startswith("_"):
                    continue
                if tool and method_name != tool:
                    continue
                docmodel = _parse_fern_method_doc(method)
                sections.append(f"### {method_name}")
                if docmodel.signature:
                    sections.append(_md_code(docmodel.signature))
                if docmodel.description:
                    sections.append(docmodel.description)
                sections.append("")
            sections.append("")
    return "\n".join(s for s in sections if s is not None)


class DocGenerator(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    list_namespaces: Callable[..., list[str]]
    list_toolsets: Callable[..., list[str]]
    list_tools: Callable[..., list[str]]
    docs: Callable[..., str]


_GENERATORS: dict[str, DocGenerator] = {}


def register_generator(name: str, generator: DocGenerator) -> None:
    _GENERATORS[name] = generator


def get_generator(name: str) -> DocGenerator:
    if name not in _GENERATORS:
        raise KeyError(f"Unknown doc generator: {name}")
    return _GENERATORS[name]


def list_generators() -> list[str]:
    return sorted(name for name in _GENERATORS.keys() if name != "fern")


def list_namespaces(generator: str = "openapi", infra: InfraManager | None = None) -> list[str]:
    gen = get_generator(generator)
    if generator in {"fern", "openapi", "mcp"}:
        return gen.list_namespaces(infra=infra)
    return gen.list_namespaces()


def list_toolsets(
    namespace: str, generator: str = "openapi", infra: InfraManager | None = None
) -> list[str]:
    gen = get_generator(generator)
    if generator in {"fern", "openapi", "mcp"}:
        return gen.list_toolsets(namespace, infra=infra)
    return gen.list_toolsets(namespace)


def list_tools(
    namespace: str,
    toolset: str,
    generator: str = "openapi",
    infra: InfraManager | None = None,
) -> list[str]:
    gen = get_generator(generator)
    if generator in {"fern", "openapi", "mcp"}:
        return gen.list_tools(namespace, toolset, infra=infra)
    return gen.list_tools(namespace, toolset)


def docs(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    generator: str = "openapi",
    infra: InfraManager | None = None,
) -> str:
    gen = get_generator(generator)
    if generator in {"fern", "openapi", "mcp"}:
        return gen.docs(namespace=namespace, toolset=toolset, tool=tool, infra=infra)
    return gen.docs(namespace_name=namespace, toolset_name=toolset, tool_name=tool)


register_generator(
    "fern",
    DocGenerator(
        list_namespaces=fern_list_namespaces,
        list_toolsets=fern_list_toolsets,
        list_tools=fern_list_tools,
        docs=fern_docs,
    ),
)
register_generator(
    "openapi",
    DocGenerator(
        list_namespaces=fern_list_namespaces,
        list_toolsets=fern_list_toolsets,
        list_tools=fern_list_tools,
        docs=fern_docs,
    ),
)
register_generator(
    "manual",
    DocGenerator(
        list_namespaces=manual_list_namespaces,
        list_toolsets=manual_list_toolsets,
        list_tools=manual_list_tools,
        docs=manual_docs,
    ),
)
register_generator(
    "mcp",
    DocGenerator(
        list_namespaces=mcp_list_namespaces,
        list_toolsets=mcp_list_toolsets,
        list_tools=mcp_list_tools,
        docs=mcp_docs,
    ),
)
