"""
Dynamic loader for Python tool modules referenced in infra.yaml.
"""

from __future__ import annotations

from importlib import util as importlib_util
from pathlib import Path
import sys

from .registry import InfraManager, PythonInfra, load_infra

__all__ = [
    "load_tools",
    "resolve_path",
    "alias_path",
    "name_module",
    "import_module",
    "store_path",
]


def name_module(alias: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in alias)
    return f"mtp_dynamic.{safe}"


def _module_name(entry: PythonInfra) -> str:
    if entry.module:
        return entry.module
    return name_module(entry.name)


def resolve_path(path_value: str | Path, *, base: Path | None = None) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (base or Path.cwd()) / path
    return path.resolve()


def alias_path(path: Path) -> str:
    return path.stem if path.suffix else path.name


def store_path(path: Path, *, base: Path | None = None) -> str:
    base = base or Path.cwd()
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def import_module(path: Path, module_name: str) -> None:
    if not path.exists():
        raise RuntimeError(f"Python file not found: {path}")
    if path.is_dir():
        init_path = path / "__init__.py"
        if not init_path.exists():
            raise RuntimeError(f"Python package missing __init__.py: {path}")
        path = init_path
    if path.suffix.lower() != ".py":
        raise RuntimeError(f"Python file expected: {path}")
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib_util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import Python file: {path}")
    module = importlib_util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise RuntimeError(f"Failed to import Python file: {exc}") from exc


def load_tools(infra: InfraManager | None = None) -> list[str]:
    infra = infra or load_infra()
    loaded: list[str] = []
    for entry in infra.python:
        path = resolve_path(entry.path)
        if not path.exists():
            continue
        if path.is_dir():
            init_path = path / "__init__.py"
            if not init_path.exists():
                continue
            path = init_path
        if path.suffix.lower() != ".py":
            continue
        module_name = _module_name(entry)
        if module_name in sys.modules:
            loaded.append(module_name)
            continue
        try:
            import_module(path, module_name)
        except Exception:
            continue
        loaded.append(module_name)
    return loaded
