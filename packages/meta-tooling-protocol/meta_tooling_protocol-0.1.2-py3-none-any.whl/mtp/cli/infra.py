"""
Infra command - generate internal SDKs from OpenAPI or gRPC.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal, NoReturn, Optional
from urllib.parse import urlparse
from urllib.request import url2pathname

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils import show_header
from mtp.core.registry import (
    InfraManager,
    OpenApiInfra,
    load_infra,
    save_infra,
    MTP_ROOT,
    REGISTRY_PATH_DEFAULT,
)
from mtp.core.docgen import docs as generate_docs


console = Console()
infra_app = typer.Typer(help="Manage infra SDKs.")

DEFAULT_FERN_ORG = "aide"
DEFAULT_FERN_CLI_VERSION = "3.35.0"
DEFAULT_FERN_PYTHON_SDK_VERSION = "4.46.6"
DEFAULT_GENERATOR_GROUP = "python-sdk"


def _fail(message: str) -> NoReturn:
    console.print(f"[red]? {message}[/red]")
    raise typer.Exit(1)


def _registry_path(path: Path | None = None) -> Path:
    return path or REGISTRY_PATH_DEFAULT


def _load_infra(path: Path | None = None) -> InfraManager:
    return load_infra(_registry_path(path))


def _save_infra(registry: InfraManager, path: Path | None = None) -> None:
    save_infra(registry, _registry_path(path))


def _infra_root(infra_path: Path | None) -> Path:
    if infra_path:
        return infra_path.parent
    return MTP_ROOT


def _sdk_root(infra_path: Path | None) -> Path:
    return _infra_root(infra_path) / "sdks"


def _find_entry(registry: InfraManager, name: str) -> Optional[OpenApiInfra]:
    entry = registry.get(name)
    return entry if isinstance(entry, OpenApiInfra) else None


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _download_url(url: str, target: Path) -> None:
    import httpx

    response = httpx.get(url, timeout=60)
    if response.status_code >= 400:
        _fail(f"Download failed: {response.status_code} {url}")
    target.write_bytes(response.content)


def _copy_source_path(source: Path, target_root: Path) -> Path:
    if source.is_dir():
        dest = target_root / source.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        return dest
    dest = target_root / source.name
    shutil.copy2(source, dest)
    return dest


def _resolve_spec_path(api_type: str, source: str, sources_root: Path) -> Path:
    parsed = urlparse(source)
    scheme = parsed.scheme.lower()
    if scheme in {"http", "https"}:
        extension = Path(parsed.path).suffix.lower()
        if not extension:
            extension = ".json" if api_type == "openapi" else ".proto"
        filename = f"{api_type}{extension}"
        target = sources_root / filename
        _download_url(source, target)
        return target
    if scheme == "file":
        if parsed.netloc not in {"", "."}:
            _fail("file URL must be local (file://...)")
        local_raw = parsed.path
        if parsed.netloc == ".":
            local_raw = local_raw.lstrip("/")
        elif len(local_raw) >= 3 and local_raw[2] == ":":
            local_raw = local_raw.lstrip("/")
        local_path = Path(url2pathname(local_raw))
        return _copy_source_path(local_path, sources_root)
    if not scheme:
        local_path = Path(source)
        return _copy_source_path(local_path, sources_root)

    _fail("source must be a URL (http/https) or file URL (file://...)")


def _infer_api_type(source: str) -> Literal["openapi", "grpc"]:
    parsed = urlparse(source)
    path = parsed.path if parsed.scheme else source
    suffix = Path(path).suffix.lower()
    return "grpc" if suffix == ".proto" else "openapi"


def _write_fern_config(fern_root: Path, org: str, version: str) -> None:
    config = {"organization": org, "version": version}
    with open(fern_root / "fern.config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def _write_generators(
    fern_root: Path,
    api_type: str,
    spec_path: Path,
    sdk_root: Path,
    group: str,
    python_sdk_version: str,
) -> None:
    spec_rel = os.path.relpath(spec_path, fern_root)
    sdk_rel = os.path.relpath(sdk_root, fern_root)
    spec_key = "openapi" if api_type == "openapi" else "proto"

    content = "\n".join(
        [
            "# yaml-language-server: $schema=https://schema.buildwithfern.dev/generators-yml.json",
            "api:",
            "  specs:",
            f"    - {spec_key}: {spec_rel}",
            f"default-group: {group}",
            "groups:",
            f"  {group}:",
            "    generators:",
            "      - name: fern-python-sdk",
            f"        version: {python_sdk_version}",
            "        output:",
            "          location: local-file-system",
            f"          path: {sdk_rel}",
            "",
        ]
    )
    with open(fern_root / "generators.yml", "w", encoding="utf-8") as f:
        f.write(content)


def _run_fern_generate(project_root: Path, group: str) -> None:
    fern_cmd = shutil.which("fern")
    if fern_cmd is None:
        _fail("SDK generator CLI not found. Install the generator CLI first.")
    if fern_cmd.lower().endswith((".cmd", ".bat")):
        cmd = ["cmd", "/c", fern_cmd, "generate", "--group", group]
    else:
        cmd = [fern_cmd, "generate", "--group", group]
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        _fail(f"SDK generate failed: {message}")


def _cleanup_paths(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def _generate_sdk(
    *,
    name: str,
    api_type: Literal["openapi", "grpc"],
    source: str,
    group: str,
    org: str,
    fern_version: str,
    python_sdk_version: str,
    infra_path: Path | None,
) -> Path:
    base_root = _infra_root(infra_path)
    cache_root = base_root / "infra"
    sources_root = cache_root / "sources" / name
    fern_project_root = cache_root / "fern" / name
    fern_root = fern_project_root / "fern"
    sdk_root = _sdk_root(infra_path) / name

    _cleanup_paths(sources_root, fern_project_root, sdk_root)
    _ensure_dir(sources_root)
    _ensure_dir(fern_root)
    _ensure_dir(sdk_root)

    console.print(f"[cyan]-> Source: {source}[/cyan]")
    spec_path_resolved = _resolve_spec_path(
        api_type=api_type,
        source=source,
        sources_root=sources_root,
    )

    _write_fern_config(fern_root, org=org, version=fern_version)
    _write_generators(
        fern_root=fern_root,
        api_type=api_type,
        spec_path=spec_path_resolved,
        sdk_root=sdk_root,
        group=group,
        python_sdk_version=python_sdk_version,
    )

    console.print(f"[cyan]-> Running SDK generator (group={group})[/cyan]")
    _run_fern_generate(fern_project_root, group=group)
    return sdk_root


@infra_app.command("add")
def infra_add(
    name: str = typer.Argument(..., help="SDK name"),
    api_type: Optional[Literal["openapi", "grpc"]] = typer.Option(
        None, "--type", help="openapi or grpc"
    ),
    source: str = typer.Option(
        ...,
        "--source",
        help="Spec URL (http/https, file://..., or local path)",
    ),
    group: str = typer.Option(DEFAULT_GENERATOR_GROUP, "--group", help="Generator group"),
    org: str = typer.Option(DEFAULT_FERN_ORG, "--org", help="Generator organization"),
    fern_version: str = typer.Option(DEFAULT_FERN_CLI_VERSION, "--generator-version"),
    python_sdk_version: str = typer.Option(
        DEFAULT_FERN_PYTHON_SDK_VERSION, "--python-sdk-version"
    ),
    infra: Optional[Path] = typer.Option(None, "--infra", help="Path to infra.yaml"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing SDK entry"),
) -> None:
    """
    Add an SDK from OpenAPI or gRPC and generate it via the built-in generator.
    """
    show_header("Infra SDK Generator", "Generate internal SDKs from OpenAPI/gRPC", console)

    registry = _load_infra(infra)
    existing = _find_entry(registry, name)
    if existing and not force:
        _fail(f"SDK already exists: {name} (use --force to overwrite)")

    resolved_type = api_type or _infer_api_type(source)
    entry = OpenApiInfra(
        name=name,
        source=source,
        type=resolved_type,
        generator=registry.config.default_generator,
    )
    sdk_root = _generate_sdk(
        name=name,
        api_type=resolved_type,
        source=source,
        group=group,
        org=org,
        fern_version=fern_version,
        python_sdk_version=python_sdk_version,
        infra_path=infra,
    )
    registry.upsert(entry)
    _save_infra(registry, infra)
    console.print(
        Panel.fit(
            f"[green]SDK generated:[/green] {name}\n"
            f"[green]Path:[/green] {sdk_root}",
            border_style="green",
        )
    )


@infra_app.command("list")
def infra_list(
    infra: Optional[Path] = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    """List generated SDKs."""
    show_header("Infra SDK Registry", "Internal SDKs", console)
    registry = _load_infra(infra)
    table = Table(show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Source", style="yellow")
    for entry in registry.sdks:
        entry_type = entry.type or _infer_api_type(entry.source)
        table.add_row(
            entry.name,
            entry_type,
            entry.source,
        )
    console.print(table)


@infra_app.command("remove")
def infra_remove(
    name: str = typer.Argument(..., help="SDK name"),
    keep_sources: bool = typer.Option(
        False, "--keep-sources", help="Keep cached sources and generator config"
    ),
    infra: Optional[Path] = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    """Remove an SDK entry and generated output."""
    show_header("Infra SDK Remove", "Remove internal SDKs", console)

    registry = _load_infra(infra)
    entry = _find_entry(registry, name)
    if not entry:
        _fail(f"SDK not found: {name}")

    base_root = _infra_root(infra)
    cache_root = base_root / "infra"
    sources_root = cache_root / "sources" / name
    fern_root = cache_root / "fern" / name
    sdk_root = _sdk_root(infra) / name

    _cleanup_paths(sdk_root)
    if not keep_sources:
        _cleanup_paths(sources_root, fern_root)

    registry.remove(name)
    _save_infra(registry, infra)
    console.print(f"[green]Removed SDK:[/green] {name}")


@infra_app.command("index")
def infra_index(
    infra: Optional[Path] = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    """Regenerate all SDKs from infra.yaml (default: ~/.mtp/infra.yaml)."""
    show_header("Infra Index", "Regenerate infra SDKs", console)
    registry = _load_infra(infra)
    for entry in registry.sdks:
        generator = entry.generator or registry.config.default_generator
        if generator not in {"openapi", "fern"}:
            console.print(f"[yellow]skip[/yellow] {entry.name} (generator={generator})")
            continue
        api_type = entry.type or _infer_api_type(entry.source)
        _generate_sdk(
            name=entry.name,
            api_type=api_type,
            source=entry.source,
            group=DEFAULT_GENERATOR_GROUP,
            org=DEFAULT_FERN_ORG,
            fern_version=DEFAULT_FERN_CLI_VERSION,
            python_sdk_version=DEFAULT_FERN_PYTHON_SDK_VERSION,
            infra_path=infra,
        )
        console.print(f"[green]Regenerated SDK:[/green] {entry.name}")


@infra_app.command("doc")
def infra_doc(
    namespace: Optional[str] = typer.Option(None, "--namespace", help="SDK namespace (e.g. cyberhub)"),
    toolset: Optional[str] = typer.Option(None, "--toolset", help="Toolset name (e.g. fingerprint)"),
    tool: Optional[str] = typer.Option(None, "--tool", help="Tool name (e.g. 获取指纹统计信息)"),
    output: Optional[Path] = typer.Option(None, "--output", help="Write docs to file"),
    infra: Optional[Path] = typer.Option(None, "--infra", help="Path to infra.yaml"),
) -> None:
    """Generate multi-level docs for infra SDKs."""
    show_header("Infra Docs", "Generate infra docs", console)
    registry = _load_infra(infra)
    if not registry.sdks:
        _fail("No infra SDKs registered. Run `mtp add <name> --openapi <spec>` first.")
    try:
        sys.path.insert(0, str(_sdk_root(infra)))
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
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Docs saved to {output}[/green]")
    else:
        console.print(content)
