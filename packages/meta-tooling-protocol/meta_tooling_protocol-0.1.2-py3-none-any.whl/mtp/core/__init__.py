"""
MTP core runtime and doc helpers.

Use Instance.exec to run Python in a persistent context. Assign the final value
to `result` to return structured data. The context persists per instance.
When using API/MCP python_exec, reuse the same instance_id to share state across calls.
Use notebook_path to persist outputs to an .ipynb file.

How to read this doc (for AI):
- The document has two top-level sections: `mtp` and `infra`.
- `mtp` contains built-in runtime tools (toolsets + builtin tools).
- `infra` lists registered external tools (cmd/python/mcp/sdk) by infra name.
- Use the tool names exactly as listed in each section.
- For python execution, call mtp.runtime.python_exec (MCP) or POST /mtp/python_exec (API).
- For infra tools, import from `mtp.infra` and pass arguments via keyword args.
- By default, imports resolve from ~/.mtp/infra.yaml; set MTP_INFRA to use a local infra.yaml.
- Progressive discovery: use `help(tool_name)` to see detailed docs, `dir(tool_name)` to list methods.

python_exec is the only external tool exposed by MTP.
All infra tools are executed by running Python code through python_exec.

### python_exec
Execute Python code and return stdout/stderr/result.

#### Example

code = "x = 1\\nresult = x + 1"
```python
def exec(self, code: 'str', timeout: 'int' = 30, notebook_path: 'Optional' = None, instance_id: 'Optional' = None) ->
'BlockingOutput'
```

Infra examples (all executed via python_exec; code runs inside python_exec):

Cmd tool (infra type: cmd):
```python
from mtp.infra import gogo

result = gogo(args=["--version"])
```

MCP tool (infra type: mcp):
```python
from mtp.infra import github

result = github.list_repos(owner="anthropics")
```

OpenAPI SDK (infra type: openapi/grpc):
```python
from mtp.infra import myapi

client = myapi.client.MyapiClient()
result = client.users.get_user(id=1)
```

Python tools (infra type: python):
```python
from mtp.infra import mytools

result = mytools.math.add(a=1, b=2)
```

Progressive discovery (explore tools dynamically):
```python
from mtp.infra import github

# Discover available methods
help(github)              # View tool documentation
dir(github)               # List available methods

# Use discovered method
result = github.list_repos(owner="anthropics")
```

Examples:
    from mtp.core import Instance

    inst = Instance()
    out = inst.exec(code="x = 1\\nresult = x + 1")
    print(out.result)

    # Persistent context across calls
    inst.exec(code="counter = 1")
    out = inst.exec(code="counter += 1\\nresult = counter")
    print(out.result)

    # Shared heap helpers
    from mtp.core import heap_set, heap_get
    heap_set("job", {"status": "ok"})
    result = heap_get("job")
"""

from .io import (
    BlockingInput,
    BlockingOutput,
    InstanceStatus,
    Traceback,
    TracebackFrame,
)
from .docgen import DocModel as _DocModel, registry as _doc_registry
from .runtime import (
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
)
from .registry import (
    InfraConfig,
    OpenApiInfra,
    PythonInfra,
    McpInfra,
    CmdInfra,
    CmdTool,
    CmdToolEntry,
    InfraItem,
    InfraManager,
    MTP_ROOT,
    REGISTRY_PATH_DEFAULT,
    BaseInfraModel,
    load_infra,
    save_infra,
)
from .docgen import (
    DocModel,
    NamespaceModel,
    Registry,
    ToolModel,
    ToolsetModel,
    DocGenerator,
    help_doc,
    gendoc,
    render_sections,
    register_generator,
    get_generator,
    list_generators,
    list_namespaces,
    list_toolsets,
    list_tools,
    docs,
    namespace,
    tool,
    toolset,
)
from .python_tools import load_tools
from . import infra as infra
from .venv import (
    venv_root,
    venv_python,
    ensure_venv,
    install_packages,
)

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
    "InfraManager",
    "InfraConfig",
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
    "REGISTRY_PATH_DEFAULT",
    "load_infra",
    "save_infra",
    "DocModel",
    "NamespaceModel",
    "Registry",
    "ToolModel",
    "ToolsetModel",
    "help_doc",
    "gendoc",
    "render_sections",
    "list_namespaces",
    "list_toolsets",
    "list_tools",
    "docs",
    "DocGenerator",
    "register_generator",
    "get_generator",
    "list_generators",
    "namespace",
    "tool",
    "toolset",
    "load_tools",
    "infra",
    "venv_root",
    "venv_python",
    "ensure_venv",
    "install_packages",
    "mcp_api_doc",
    "mtp_doc",
    "runtime_doc",
    "infra_doc",
    "exec_doc",
]


def mcp_api_doc() -> str:
    return "Execute Python code in a persistent runtime. Use `from mtp.infra import <tool>` to access registered tools."


def mtp_doc() -> str:
    return (__doc__ or "").strip()


_ns = _doc_registry.get_namespace("mtp")
if _ns:
    _ns.docmodel = _DocModel.from_docstring(__doc__ or "", "mtp")


def _strip_first_heading(doc: str) -> str:
    lines = doc.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return doc


def runtime_doc() -> str:
    return _strip_first_heading(docs(namespace="mtp", toolset="runtime", generator="manual").strip())


def infra_doc(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra_path: "Path | None" = None,
) -> str:
    from pathlib import Path

    registry = load_infra(infra_path if infra_path else None)
    sections = []

    def _match(ns: str, ts: str | None, t: str) -> bool:
        if namespace and ns != namespace:
            return False
        if toolset is not None and ts != toolset:
            return False
        if tool is not None and t != tool:
            return False
        return True

    # Generate SDK documentation (with filtering)
    if registry.sdks and not any([namespace, toolset, tool]):
        import sys as _sys
        _sys.path.insert(0, str(MTP_ROOT / "sdks"))
        sdk_doc = gendoc(registry).strip()
        if sdk_doc:
            sections.append(sdk_doc)

    # Generate cmd tool documentation
    if registry.cmd:
        cmd_docs = []
        for entry in registry.cmd:
            for tool_entry in entry.tools:
                if not any([namespace, toolset, tool]) or _match(entry.name, None, tool_entry.name):
                    # Use full description to provide complete usage examples
                    desc = tool_entry.description or f"Command-line tool: {tool_entry.command}"

                    call = (
                        f"result = {entry.name}(args=[...])"
                        if tool_entry.name == entry.name
                        else f"result = {entry.name}.{tool_entry.name}(args=[...])"
                    )
                    cmd_docs.append(
                        "\n".join(
                            [
                                f"## {entry.name}",
                                f"### {tool_entry.name}",
                                desc,
                                "```python",
                                f"from mtp.infra import {entry.name}",
                                call,
                                "```",
                            ]
                        )
                    )
        if cmd_docs:
            sections.append("# Cmd Tools\n\n" + "\n\n".join(cmd_docs))

    # Generate MCP tool documentation
    if registry.mcps:
        mcp_docs = []
        for entry in registry.mcps:
            if not any([namespace, toolset, tool]) or _match(entry.name, None, entry.name):
                desc = entry.description or f"MCP server: {entry.name}"
                mcp_docs.append(f"## {entry.name}\n{desc}\n```python\nfrom mtp import {entry.name}\nresult = {entry.name}.tool_name(arg=value)\n```")
        if mcp_docs:
            sections.append("# MCP Tools\n\n" + "\n\n".join(mcp_docs))

    if not sections:
        if any([namespace, toolset, tool]):
            return "No matching infra tools found."
        return "No infra tools registered. Run `mtp add <name>` to register tools."

    return "\n\n".join(sections)


def exec_doc(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra_path: "Path | None" = None,
) -> str:
    return render_sections(
        [
            ("MCP/API", mcp_api_doc()),
            ("Infra", infra_doc(namespace, toolset, tool, infra_path)),
            ("MTP", mtp_doc()),
            ("Runtime", runtime_doc()),
        ]
    )


