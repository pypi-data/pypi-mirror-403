"""
MTP CLI.
"""

from __future__ import annotations

import os
import shlex
import shutil
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, NoReturn

import typer
from rich.console import Console

from . import infra as infra_cli
from .utils import show_header
from mtp.core.docgen import docs as generate_docs, help_doc as generate_help
from mtp.core.mcp_registry import (
    MCP_REGISTRY_BASE,
    InputDef,
    PackageDef,
    RemoteDef,
    ServerDef,
    ServerSearchItem,
    fetch_server,
    fetch_servers,
)
from mtp.core.registry import (
    CmdInfra,
    CmdTool,
    InfraManager,
    McpInfra,
    OpenApiInfra,
    PythonInfra,
    load_infra,
    save_infra,
    MTP_ROOT,
    REGISTRY_PATH_DEFAULT,
)
from mtp.core.python_tools import (
    import_module,
    name_module,
    resolve_path,
    alias_path,
    store_path,
)
from mtp.core.venv import ensure_venv, install_packages, venv_root
from mtp.api import APIAdapter
from mtp.mcp_server import MCPAdapter
from mtp.core.mcp_client import list_tools_sync


console = Console()
err_console = Console(stderr=True)
app = typer.Typer(name="mtp", help="MTP CLI", add_completion=False)
doc_app = typer.Typer(help="Generate docs", invoke_without_command=True)

app.add_typer(doc_app, name="doc")


def _fail(message: str) -> NoReturn:
    err_console.print(f"[red]? {message}[/red]")
    raise typer.Exit(1)


def _normalize_transport(value: str | None) -> str | None:
    if value is None:
        return None
    norm = value.lower().replace("_", "-")
    if norm in {"streamhttp", "stream-http", "streamable-http", "http"}:
        return "streamable-http"
    if norm == "stdio":
        return "stdio"
    _fail("transport must be stdio or streamhttp")
    return None


def _parse_kv(items: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            _fail(f"Invalid KEY=VALUE pair: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            _fail(f"Invalid KEY=VALUE pair: {item}")
        result[key] = value
    return result


def _alias_cmd(command: str) -> str:
    if not command:
        return "cmd"
    tokens = shlex.split(command, posix=os.name != "nt")
    if not tokens:
        return command
    return Path(tokens[0]).stem or tokens[0]


def _split_cmd_value(command: str) -> tuple[str, list[str]]:
    if not command:
        _fail("Command is required.")
    tokens = shlex.split(command, posix=os.name != "nt")
    if not tokens:
        _fail("Command is required.")
    return tokens[0], tokens[1:]


def _format_cmd_value(tokens: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(tokens)
    return shlex.join(tokens)


def _resolve_cmd_path(cmd_name: str) -> Path | None:
    candidate = Path(cmd_name).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.exists() and candidate.is_file():
        return candidate.resolve()
    return None


def _infra_root(infra_path: Path | None) -> Path:
    if infra_path:
        return infra_path.parent
    return MTP_ROOT


def _sdk_root(infra_path: Path | None) -> Path:
    return _infra_root(infra_path) / "sdks"


def _infra_cmd_root(infra_path: Path | None) -> Path:
    return _infra_root(infra_path) / "infra" / "cmd"


def _cleanup_paths(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def _remove_sdk_output(name: str, infra_path: Path | None, keep_sources: bool) -> None:
    base_root = _infra_root(infra_path)
    cache_root = base_root / "infra"
    sources_root = cache_root / "sources" / name
    fern_root = cache_root / "fern" / name
    sdk_root = _sdk_root(infra_path) / name
    _cleanup_paths(sdk_root)
    if not keep_sources:
        _cleanup_paths(sources_root, fern_root)




def _args_from_inputs(items: list[InputDef] | None) -> list[str]:
    args: list[str] = []
    for item in items or []:
        name = item.name.strip()
        value = item.value
        if name:
            args.append(name)
            if value not in (None, ""):
                args.append(str(value))
        elif value not in (None, ""):
            args.append(str(value))
    return args


def _pick_server(
    candidates: list[ServerSearchItem],
    query: str,
) -> tuple[ServerSearchItem, list[ServerSearchItem]]:
    if not candidates:
        _fail(f"No MCP servers found for: {query}")
    query_norm = query.lower()
    scored: list[tuple[tuple[int, int], ServerSearchItem]] = []
    for item in candidates:
        name = item.server.name
        full = name.lower()
        short = full.split("/")[-1]
        score = 10
        if full == query_norm:
            score = 0
        elif short == query_norm:
            score = 0
        elif short == f"{query_norm}-mcp":
            score = 1
        elif short.startswith(query_norm):
            score = 2
        elif query_norm in short:
            score = 3
        scored.append(((score, len(short)), item))
    scored.sort(key=lambda item: item[0])
    best = scored[0][1]
    others = [server for _, server in scored[1:]]
    return best, others


def _pick_package(
    packages: list[PackageDef],
    *,
    transport: str,
    registry_type: str | None,
) -> PackageDef | None:
    candidates = [
        pkg
        for pkg in packages
        if pkg.transport is not None and pkg.transport.type == transport
    ]
    if registry_type:
        candidates = [pkg for pkg in candidates if pkg.registryType == registry_type]
    if not candidates:
        return None
    priority = ["pypi", "npm", "mcpb", "oci", "nuget"]
    for reg in priority:
        for pkg in candidates:
            if pkg.registryType == reg:
                return pkg
    return candidates[0]


def _pick_remote(remotes: list[RemoteDef], transport: str) -> RemoteDef | None:
    candidates = [remote for remote in remotes if remote.type == transport]
    return candidates[0] if candidates else None


def _build_stdio_command(package: PackageDef) -> tuple[str | None, list[str]]:
    registry_type = package.registryType
    runtime_hint = package.runtimeHint
    runtime_args = _args_from_inputs(package.runtimeArguments)
    package_args = _args_from_inputs(package.packageArguments)
    identifier = package.identifier

    if registry_type == "npm":
        cmd = runtime_hint or "npx"
        args = runtime_args + ([identifier] if identifier else []) + package_args
        return cmd, args
    if registry_type == "pypi":
        cmd = runtime_hint or "python"
        args = runtime_args + (["-m", identifier] if identifier else []) + package_args
        return cmd, args
    if registry_type == "oci":
        cmd = runtime_hint or "docker"
        args = runtime_args or ["run", "--rm"]
        if identifier:
            args = args + [identifier]
        args += package_args
        return cmd, args

    cmd = runtime_hint
    args = runtime_args + package_args
    if identifier:
        args = args + [identifier]
    return cmd, args


def _apply_defaults(defs: list[InputDef], target: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for item in defs:
        name = item.name
        value = item.value
        if name not in target and value not in (None, ""):
            target[name] = str(value)
        if item.isRequired and name not in target:
            missing.append(name)
    return missing


def _first_line(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().splitlines()[0]


def _infer_api_type(source: str) -> str:
    parsed = urlparse(source)
    path = parsed.path if parsed.scheme else source
    return "grpc" if path.lower().endswith(".proto") else "openapi"


def _list_infra_lines(registry: InfraManager) -> list[str]:
    lines: list[str] = []
    for entry in registry.sdks:
        entry_type = entry.type or _infer_api_type(entry.source)
        lines.append(f"sdk {entry.name} ({entry_type}) - source={entry.source}")
    for entry in registry.mcps:
        details: list[str] = []
        if entry.server:
            server = entry.server
            if entry.version:
                server = f"{server}@{entry.version}"
            details.append(f"server={server}")
        if entry.package:
            details.append(f"package={entry.package}")
        if entry.url:
            details.append(f"url={entry.url}")
        elif entry.command:
            cmd = " ".join([entry.command, *entry.args]).strip()
            details.append(f"command={cmd}")
        desc = _first_line(entry.description)
        if desc:
            details.append(f"desc={desc}")
        summary = ", ".join(details) if details else "registered"
        lines.append(f"mcp {entry.name} ({entry.transport}) - {summary}")
    for entry in registry.python:
        details = [f"path={entry.path}"]
        if entry.module:
            details.append(f"module={entry.module}")
        desc = _first_line(entry.description)
        if desc:
            details.append(f"desc={desc}")
        lines.append(f"python {entry.name} - {', '.join(details)}")
    for entry in registry.cmd:
        if len(entry.tools) == 1:
            tool = entry.tools[0]
            cmd = " ".join([tool.command, *tool.args]).strip()
            details = [f"command={cmd}"]
            if tool.cwd:
                details.append(f"cwd={tool.cwd}")
            if tool.shell:
                details.append("shell=true")
            desc = _first_line(tool.description)
            if desc:
                details.append(f"desc={desc}")
            lines.append(f"cmd {entry.name} - {', '.join(details)}")
        else:
            tool_names = ",".join(tool.name for tool in entry.tools)
            lines.append(f"cmd {entry.name} - tools={tool_names}")
    return lines


@app.command()
def install(
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
    skip_openapi: bool = typer.Option(False, "--skip-openapi", help="Skip OpenAPI SDK generation"),
    skip_mcp: bool = typer.Option(False, "--skip-mcp", help="Skip MCP prefetch"),
    skip_deps: bool = typer.Option(False, "--skip-deps", help="Skip infra dependency install"),
) -> None:
    """
    Initialize infra from infra.yaml.
    """
    show_header("MTP Install", "Initialize infra (OpenAPI, MCP, deps)", console)
    registry = load_infra(infra)
    did_work = False

    if registry.dependency and not skip_deps:
        venv_root_path = venv_root(True)
        try:
            venv_python = ensure_venv(venv_root_path)
            install_packages(venv_python, registry.dependency)
        except RuntimeError as exc:
            _fail(str(exc))
        console.print(f"[green]Infra deps installed:[/green] {' '.join(registry.dependency)}")
        console.print(f"[green]Venv:[/green] {venv_root_path}")
        did_work = True

    if registry.sdks and not skip_openapi:
        try:
            infra_cli.infra_index(infra=infra)
        except Exception as exc:
            _fail(f"Infra OpenAPI init failed: {exc}")
        did_work = True

    if registry.mcps and not skip_mcp:
        failures: list[str] = []
        for entry in registry.mcps:
            try:
                list_tools_sync(entry)
            except Exception as exc:
                failures.append(f"{entry.name}: {exc}")
        if failures:
            console.print("[yellow]Some MCP servers failed to prefetch:[/yellow]")
            for item in failures:
                console.print(f"[yellow]- {item}[/yellow]")
        else:
            console.print("[green]MCP servers prefetched.[/green]")
        did_work = True

    if not did_work:
        console.print("[yellow]Nothing to install. infra.yaml is empty.[/yellow]")


@app.command("list")
def list_infra(
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    """List infra registry entries."""
    show_header("MTP Infra", "List infra entries", console)
    registry = load_infra(infra)
    lines = _list_infra_lines(registry)
    if not lines:
        console.print("[yellow]No infra entries registered.[/yellow]")
        return
    for line in lines:
        console.print(line)


@app.command("remove")
def remove_infra(
    name: str = typer.Argument(..., help="Infra name to remove"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
    keep_sources: bool = typer.Option(
        False, "--keep-sources", help="Keep cached sources and generator config for SDKs"
    ),
) -> None:
    """Remove infra registry entries by name."""
    show_header("MTP Remove", "Remove infra entries", console)
    registry = load_infra(infra)
    entry = registry.get(name)
    if entry is None:
        _fail(f"Infra entry not found: {name}")
    if isinstance(entry, OpenApiInfra):
        _remove_sdk_output(name, infra, keep_sources)
    registry.remove(name)
    save_infra(registry, infra)
    console.print(f"[green]Removed {entry.type}:[/green] {name}")


def _parse_pip_targets(args: list[str]) -> list[str]:
    if not args or args[0] != "install":
        return []
    targets: list[str] = []
    expect_value = {
        "-r",
        "--requirement",
        "-c",
        "--constraint",
        "-e",
        "--editable",
        "-i",
        "--index-url",
        "--extra-index-url",
        "-f",
        "--find-links",
        "--platform",
        "--python-version",
        "--implementation",
        "--abi",
        "--target",
        "-t",
        "--prefix",
        "--root",
        "--config-settings",
        "--trusted-host",
        "--log",
        "--cache-dir",
        "--progress-bar",
    }
    skip_next = False
    for item in args[1:]:
        if skip_next:
            skip_next = False
            continue
        if item in expect_value:
            skip_next = True
            continue
        if item.startswith("-"):
            continue
        targets.append(item)
    return targets


@app.command("pip", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def pip_cmd(
    ctx: typer.Context,
    args: list[str] | None = typer.Argument(None, help="Pip arguments"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
    global_: bool = typer.Option(True, "--global/--local", help="Use mtp global venv"),
) -> None:
    """
    Run pip inside the mtp venv and record installed packages.
    """
    show_header("MTP Pip", "Run pip inside mtp venv", console)
    full_args = list(args or []) + list(ctx.args)
    if not full_args:
        _fail("No pip arguments provided.")
    venv_root_path = venv_root(global_)
    try:
        venv_python = ensure_venv(venv_root_path)
    except RuntimeError as exc:
        _fail(str(exc))

    result = subprocess.run(
        [str(venv_python), "-m", "pip", *full_args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        _fail(f"pip failed: {detail}")

    targets = _parse_pip_targets(full_args)
    if targets:
        registry = load_infra(infra)
        existing = set(registry.dependency)
        for item in targets:
            if item not in existing:
                registry.dependency.append(item)
                existing.add(item)
        save_infra(registry, infra)
        console.print(f"[green]Dependencies recorded:[/green] {', '.join(targets)}")

    console.print(result.stdout.strip() or "[green]pip ok[/green]")


def _add_openapi(
    *,
    name: str,
    api_type: str | None,
    source: str,
    group: str,
    org: str,
    generator_version: str,
    python_sdk_version: str,
    infra_path: Path | None,
    force: bool,
) -> None:
    infra_cli.infra_add(
        name=name,
        api_type=api_type,
        source=source,
        group=group,
        org=org,
        fern_version=generator_version,
        python_sdk_version=python_sdk_version,
        infra=infra_path,
        force=force,
    )


def _add_mcp(
    *,
    query: str,
    name: str | None,
    server: str | None,
    version: str,
    transport: str | None,
    registry_type: str | None,
    command: str | None,
    arg: list[str] | None,
    env: list[str] | None,
    header: list[str] | None,
    registry_base: str,
    infra_path: Path | None,
    force: bool,
) -> None:
    show_header("MCP Add", "Register MCP servers from the registry", console)
    registry = load_infra(infra_path)
    alias = name or query
    existing = registry.get(alias)
    if existing and not force:
        _fail(f"Infra entry already exists: {alias} (use --force to overwrite)")

    registry_type = registry_type.lower() if registry_type else None

    try:
        if server:
            server_data = fetch_server(server_name=server, version=version, registry_base=registry_base)
        else:
            matches = fetch_servers(search=query, version=version, registry_base=registry_base)
            best, others = _pick_server(matches, query)
            if others:
                other_names = [item.server.name for item in others]
                if other_names:
                    console.print(f"[yellow]Multiple matches found.[/yellow] Selected: {best.server.name}")
                    console.print(f"[yellow]Other matches:[/yellow] {', '.join(other_names)}")
            server_data = fetch_server(
                server_name=best.server.name,
                version=version,
                registry_base=registry_base,
            )
    except Exception as exc:
        _fail(f"Failed to query MCP registry: {exc}")

    packages = server_data.packages
    remotes = server_data.remotes
    desired_transport = _normalize_transport(transport)

    if desired_transport is None:
        if any(pkg.transport is not None and pkg.transport.type == "stdio" for pkg in packages):
            desired_transport = "stdio"
        elif any(remote.type == "streamable-http" for remote in remotes):
            desired_transport = "streamable-http"
        elif packages:
            desired_transport = packages[0].transport.type if packages[0].transport else "stdio"
        elif remotes:
            desired_transport = remotes[0].type
        else:
            _fail("Registry entry has no packages or remotes to install.")

    if desired_transport not in {"stdio", "streamable-http"}:
        _fail(f"Unsupported MCP transport: {desired_transport}")

    selected_package = _pick_package(packages, transport=desired_transport, registry_type=registry_type)
    selected_remote = _pick_remote(remotes, desired_transport)
    if desired_transport == "streamable-http" and selected_remote is not None:
        selected_package = None

    if desired_transport == "streamable-http" and selected_remote is None and selected_package is None:
        _fail("No streamable-http endpoint found for this server.")
    if desired_transport == "stdio" and selected_package is None:
        _fail("No stdio package found for this server.")

    env_values = _parse_kv(env)
    header_values = _parse_kv(header)

    missing_env: list[str] = []
    header_defs: list[InputDef] = []
    url: str | None = None
    if selected_package:
        missing_env = _apply_defaults(selected_package.environmentVariables, env_values)
        if selected_package.transport:
            header_defs = selected_package.transport.headers
            url = selected_package.transport.url
    if selected_remote:
        header_defs = selected_remote.headers
        url = selected_remote.url
    missing_headers = _apply_defaults(header_defs, header_values)

    if missing_env:
        console.print(f"[yellow]Missing required env:[/yellow] {', '.join(missing_env)}")
    if missing_headers:
        console.print(f"[yellow]Missing required headers:[/yellow] {', '.join(missing_headers)}")

    cmd = command
    args: list[str] = []
    if desired_transport == "stdio":
        if selected_package:
            inferred_cmd, inferred_args = _build_stdio_command(selected_package)
            cmd = cmd or inferred_cmd
            args = inferred_args
        if arg:
            args = args + arg
        if not cmd:
            _fail("Unable to determine stdio command. Provide --command explicitly.")

    if desired_transport == "streamable-http" and not url:
        _fail("streamable-http transport requires a URL.")
    metadata: dict[str, Any] = {}
    if selected_package:
        metadata["package"] = selected_package.model_dump(exclude_none=True)
    if selected_remote:
        metadata["remote"] = selected_remote.model_dump(exclude_none=True)

    entry = McpInfra(
        type="mcp",
        name=alias,
        transport=desired_transport or "stdio",
        command=cmd,
        args=args,
        env=env_values,
        url=url,
        headers=header_values,
        server=server_data.name,
        version=server_data.version,
        description=server_data.description,
        registry_type=selected_package.registryType if selected_package else None,
        package=selected_package.identifier if selected_package else None,
        metadata=metadata,
    )

    registry.upsert(entry)
    save_infra(registry, infra_path)
    console.print(f"[green]Registered MCP:[/green] {alias}")
    console.print(f"[green]Transport:[/green] {entry.transport}")
    if entry.command:
        console.print(f"[green]Command:[/green] {entry.command} {' '.join(entry.args)}")
    if entry.url:
        console.print(f"[green]URL:[/green] {entry.url}")


def _add_python(
    *,
    path: Path,
    name: str | None,
    module: str | None,
    infra_path: Path | None,
    force: bool,
) -> None:
    show_header("Python Add", "Register Python tools", console)
    registry = load_infra(infra_path)

    resolved = resolve_path(path.expanduser())
    alias = name or alias_path(resolved)
    module_name = module or name_module(alias)

    existing = registry.get(alias)
    if existing and not force:
        _fail(f"Infra entry already exists: {alias} (use --force to overwrite)")

    try:
        import_module(resolved, module_name)
    except Exception as exc:
        _fail(str(exc))

    stored_path = store_path(resolved, base=Path.cwd())

    entry = PythonInfra(type="python", name=alias, path=stored_path, module=module_name)
    registry.upsert(entry)
    save_infra(registry, infra_path)

    console.print(f"[green]Registered Python module:[/green] {alias}")
    console.print(f"[green]Path:[/green] {stored_path}")


def _capture_cmd_help(
    *,
    cmd_name: str,
    cmd_args: list[str],
    base_args: list[str],
    shell: bool,
    cwd: str | None,
    env: dict[str, str],
) -> str | None:
    help_tokens = [cmd_name, *cmd_args, *base_args, "--help"]
    exec_env = dict(os.environ)
    exec_env.update(env)
    try:
        if shell:
            cmd_str = _format_cmd_value(help_tokens)
            result = subprocess.run(
                cmd_str,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd,
                env=exec_env,
                shell=True,
            )
        else:
            result = subprocess.run(
                help_tokens,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd,
                env=exec_env,
                shell=False,
            )
    except Exception:
        return None
    output = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if err:
        output = "\n".join([output, err]).strip() if output else err
    return output or None


def _add_cmd(
    *,
    target: str,
    name: str | None,
    command: str | None,
    arg: list[str] | None,
    env: list[str] | None,
    cwd: str | None,
    shell: bool,
    description: str | None,
    infra_path: Path | None,
    force: bool,
) -> None:
    show_header("Cmd Add", "Register command tools", console)
    registry = load_infra(infra_path)

    if not command:
        _fail("Command is required.")
    cmd_value = command
    cmd_name, cmd_args = _split_cmd_value(command)
    env_values = _parse_kv(env)
    alias = name or target
    existing = registry.get(alias)
    if existing and not force:
        _fail(f"Infra entry already exists: {alias} (use --force to overwrite)")

    cmd_path = _resolve_cmd_path(cmd_name)
    stored_path: Path | None = None
    if cmd_path:
        which_path = shutil.which(cmd_path.name)
        if which_path:
            try:
                if Path(which_path).resolve().samefile(cmd_path):
                    cmd_path = None
            except FileNotFoundError:
                pass
        if cmd_path:
            path_env = os.environ.get("PATH", "")
            path_items = [p.strip().lower() for p in path_env.split(os.pathsep) if p.strip()]
            if str(cmd_path.parent).lower() in path_items:
                cmd_path = None
        if cmd_path:
            cmd_root = _infra_cmd_root(infra_path)
            dest_dir = cmd_root / alias
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / cmd_path.name
            same_target = False
            if dest_path.exists():
                try:
                    same_target = dest_path.resolve() == cmd_path
                except FileNotFoundError:
                    same_target = False
            if dest_path.exists() and not same_target:
                if not force:
                    _fail(f"Command file already exists: {dest_path} (use --force to overwrite)")
                if dest_path.is_dir():
                    shutil.rmtree(dest_path)
                else:
                    dest_path.unlink()
            if not same_target:
                try:
                    shutil.copy2(str(cmd_path), str(dest_path))
                except Exception as exc:
                    _fail(f"Failed to copy command to infra: {exc}")
            stored_path = dest_path
            cmd_name = str(dest_path)
    else:
        if shutil.which(cmd_name) is None:
            _fail(f"Command not found: {cmd_name} (provide a file path or install it)")

    cmd_value = _format_cmd_value([cmd_name, *cmd_args])
    base_args = arg or []
    help_text = _capture_cmd_help(
        cmd_name=cmd_name,
        cmd_args=cmd_args,
        base_args=base_args,
        shell=shell,
        cwd=cwd,
        env=env_values,
    )
    desc = description or f"Run command: {cmd_value}"
    if help_text and "#### Help" not in desc:
        desc = f"{desc}\n\n#### Help\n\n```text\n{help_text}\n```"

    tool = CmdTool(
        name=alias,
        command=cmd_value,
        args=base_args,
        cwd=cwd,
        env=env_values,
        shell=shell,
        description=desc,
    )
    entry = CmdInfra(type="cmd", name=alias, tools=[tool])
    registry.upsert(entry)
    save_infra(registry, infra_path)

    console.print(f"[green]Registered command:[/green] {alias}")
    console.print(f"[green]Command:[/green] {cmd_value} {' '.join(entry.args)}")
    if stored_path:
        console.print(f"[green]Command stored:[/green] {stored_path}")


@app.command()
def add(
    target: str = typer.Argument(..., help="Infra name, MCP query, or command"),
    python_path: str | None = typer.Option(None, "--python", help="Python file or package path"),
    openapi_source: str | None = typer.Option(None, "--openapi", help="OpenAPI/gRPC spec URL or path"),
    cmd_value: str | None = typer.Option(None, "--cmd", help="Command string or executable path"),
    # OpenAPI options
    api_type: str | None = typer.Option(None, "--type", help="openapi or grpc"),
    group: str = typer.Option(infra_cli.DEFAULT_GENERATOR_GROUP, "--group", help="Generator group"),
    org: str = typer.Option(infra_cli.DEFAULT_FERN_ORG, "--org", help="Generator organization"),
    generator_version: str = typer.Option(infra_cli.DEFAULT_FERN_CLI_VERSION, "--generator-version"),
    python_sdk_version: str = typer.Option(infra_cli.DEFAULT_FERN_PYTHON_SDK_VERSION, "--python-sdk-version"),
    # MCP options
    name: str | None = typer.Option(None, "--name", help="Local alias for the server/module"),
    server: str | None = typer.Option(None, "--server", help="Exact registry server name"),
    version: str = typer.Option("latest", "--version", help="Registry version to resolve"),
    transport: str | None = typer.Option(None, "--transport", help="stdio or streamhttp"),
    registry_type: str | None = typer.Option(None, "--registry-type", help="Prefer a registry type (npm/pypi/oci/nuget/mcpb)"),
    command: str | None = typer.Option(None, "--command", help="Override stdio command for MCP"),
    arg: list[str] = typer.Option(None, "--arg", help="Extra args for stdio command or --cmd"),
    env: list[str] = typer.Option(None, "--env", help="KEY=VALUE for environment variables"),
    header: list[str] = typer.Option(None, "--header", help="KEY=VALUE for HTTP headers"),
    registry_base: str = typer.Option(MCP_REGISTRY_BASE, "--registry-base", help="Registry API base URL"),
    module: str | None = typer.Option(None, "--module", help="Import module name"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory for command tools"),
    shell: bool = typer.Option(False, "--shell", help="Run command through the shell"),
    description: str | None = typer.Option(None, "--description", help="Description for command tools"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing entry"),
) -> None:
    """
    Add MCP, OpenAPI/gRPC, Python, or command tools.
    """
    openapi_value = openapi_source
    if cmd_value is not None and command:
        _fail("Use --cmd for command tools; --command is for MCP.")
    flags = [bool(python_path), bool(openapi_value), cmd_value is not None]
    if sum(1 for flag in flags if flag) > 1:
        _fail("Choose only one of --python, --openapi, or --cmd.")
    if openapi_value is not None:
        if not openapi_value:
            _fail("OpenAPI source is required.")
        _add_openapi(
            name=target,
            api_type=api_type,
            source=openapi_value,
            group=group,
            org=org,
            generator_version=generator_version,
            python_sdk_version=python_sdk_version,
            infra_path=infra,
            force=force,
        )
        return
    if python_path:
        _add_python(
            path=Path(python_path),
            name=name or target,
            module=module,
            infra_path=infra,
            force=force,
        )
        return
    if cmd_value is not None:
        if not cmd_value:
            _fail("Command is required.")
        _add_cmd(
            target=target,
            name=name,
            command=cmd_value,
            arg=arg,
            env=env,
            cwd=cwd,
            shell=shell,
            description=description,
            infra_path=infra,
            force=force,
        )
        return
    _add_mcp(
        query=target,
        name=name,
        server=server,
        version=version,
        transport=transport,
        registry_type=registry_type,
        command=command,
        arg=arg,
        env=env,
        header=header,
        registry_base=registry_base,
        infra_path=infra,
        force=force,
    )


@doc_app.callback()
def doc_callback(
    ctx: typer.Context,
    namespace: str | None = typer.Option(None, "--namespace", help="Namespace name"),
    toolset: str | None = typer.Option(None, "--toolset", help="Toolset name"),
    tool: str | None = typer.Option(None, "--tool", help="Tool name"),
    output: Path | None = typer.Option(None, "--output", help="Write docs to file"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    _doc_auto(namespace=namespace, toolset=toolset, tool=tool, output=output, infra_path=infra)


@doc_app.command("openapi")
def doc_openapi(
    namespace: str | None = typer.Option(None, "--namespace", help="SDK namespace (e.g. cyberhub)"),
    toolset: str | None = typer.Option(None, "--toolset", help="Toolset name (e.g. fingerprint)"),
    tool: str | None = typer.Option(None, "--tool", help="Tool name (e.g. get_fingerprint_stats)"),
    output: Path | None = typer.Option(None, "--output", help="Write docs to file"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    _doc_openapi(namespace=namespace, toolset=toolset, tool=tool, output=output, infra_path=infra)


def _doc_openapi(
    *,
    namespace: str | None,
    toolset: str | None,
    tool: str | None,
    output: Path | None,
    infra_path: Path | None,
) -> None:
    show_header("Infra Docs", "Generate infra docs (OpenAPI/gRPC)", console)
    registry = load_infra(infra_path)
    if not registry.sdks:
        _fail("No infra SDKs registered. Run `mtp add <name> --openapi <spec>` first.")
    try:
        sys.path.insert(0, str(_sdk_root(infra_path)))
        content = generate_docs(
            namespace=namespace,
            toolset=toolset,
            tool=tool,
            generator="openapi",
            infra=registry,
        )
    except Exception as exc:
        _fail(f"Failed to generate docs: {exc}")
    if not content.strip():
        _fail("No docs generated. Check that the SDK package exists and is importable.")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Docs saved to {output}[/green]")
    else:
        console.print(content)


def _doc_auto(
    *,
    namespace: str | None,
    toolset: str | None,
    tool: str | None,
    output: Path | None,
    infra_path: Path | None,
) -> None:
    show_header("Infra Docs", "Generate infra docs", console)
    registry = load_infra(infra_path)
    try:
        if registry.sdks:
            sys.path.insert(0, str(_sdk_root(infra_path)))
        content = generate_help(
            namespace=namespace,
            toolset=toolset,
            tool=tool,
            infra=registry,
        )
    except Exception as exc:
        _fail(f"Failed to generate docs: {exc}")

    if not content.strip():
        _fail("No docs generated. Check that the namespace exists and is importable.")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Docs saved to {output}[/green]")
    else:
        console.print(content)


@doc_app.command("mcp")
def doc_mcp(
    namespace: str | None = typer.Option(None, "--namespace", help="MCP namespace (alias)"),
    tool: str | None = typer.Option(None, "--tool", help="Tool name"),
    output: Path | None = typer.Option(None, "--output", help="Write docs to file"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    show_header("MCP Docs", "Generate MCP docs via MCP client", console)
    registry = load_infra(infra)
    try:
        content = generate_docs(
            namespace=namespace,
            toolset=None,
            tool=tool,
            generator="mcp",
            infra=registry,
        )
    except Exception as exc:
        _fail(f"Failed to generate MCP docs: {exc}")

    if not content.strip():
        _fail("No MCP docs generated. Check MCP server configuration.")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Docs saved to {output}[/green]")
    else:
        console.print(content)


@app.command()
def api(
    host: str = typer.Option("127.0.0.1", "--host", help="HTTP host"),
    port: int = typer.Option(8000, "--port", help="HTTP port"),
    path: str = typer.Option("", "--path", help="HTTP base path"),
) -> None:
    """
    Serve mtp as a FastAPI app.
    """
    show_header("MTP API", "Serve mtp HTTP API", console)
    try:
        import uvicorn
    except Exception as exc:
        _fail(f"uvicorn is required for mtp api: {exc}")
    try:
        app_instance = APIAdapter().app(path=path)
    except Exception as exc:
        _fail(f"Failed to create API app: {exc}")
    uvicorn.run(app_instance, host=host, port=port)


@app.command()
def mcp(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        help="Server transport to use (stdio/http)",
    ),
    aggregate: bool = typer.Option(
        False,
        "--aggregate",
        help="Register all @tool functions as MCP tools",
    ),
    namespace: str | None = typer.Option(None, "--namespace", help="Limit tools to a namespace"),
    toolset: str | None = typer.Option(None, "--toolset", help="Limit tools to a toolset"),
    tool: str | None = typer.Option(None, "--tool", help="Limit tools to a tool name"),
    infra: Path | None = typer.Option(None, "--infra", help="Path to infra.yaml"),
    host: str = typer.Option("0.0.0.0", "--host", help="HTTP host"),
    port: int = typer.Option(8000, "--port", help="HTTP port"),
    path: str = typer.Option("", "--path", help="HTTP base path"),
) -> None:
    """
    Serve mtp as an MCP server.
    """
    if transport != "stdio":
        show_header("MTP MCP", "Serve mtp MCP server", console)
    mtp = MCPAdapter(
        aggregate=aggregate,
        namespace=namespace,
        toolset=toolset,
        tool=tool,
        infra_path=infra,
    )
    if transport == "stdio":
        try:
            mtp.serve_stdio()
        except Exception as exc:
            _fail(str(exc))
        return
    if transport == "http":
        try:
            mtp.serve_http(host=host, port=port, path=path)
        except Exception as exc:
            _fail(str(exc))
        return
    _fail("transport must be stdio or http")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
