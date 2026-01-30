"""
Venv management helpers for MTP.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

from .registry import MTP_ROOT


def venv_root(use_global: bool) -> Path:
    if use_global:
        return MTP_ROOT / ".venv"
    return Path.cwd() / ".venv"


def venv_python(venv_root_path: Path) -> Path:
    if os.name == "nt":
        return venv_root_path / "Scripts" / "python.exe"
    return venv_root_path / "bin" / "python"


def ensure_venv(venv_root_path: Path) -> Path:
    if not venv_root_path.exists():
        venv_root_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_root_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"venv create failed: {detail}")
    venv_python_path = venv_python(venv_root_path)
    if not venv_python_path.exists():
        raise RuntimeError(f"venv python not found: {venv_python_path}")
    return venv_python_path


def install_packages(venv_python_path: Path, packages: list[str]) -> None:
    result = subprocess.run(
        [str(venv_python_path), "-m", "pip", "install", *packages],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"pip install failed: {detail}")
