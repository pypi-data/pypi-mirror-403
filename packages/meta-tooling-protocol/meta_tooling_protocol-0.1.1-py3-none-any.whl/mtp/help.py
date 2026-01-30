"""
Shared help text for MTP adapters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .core import exec_doc

__all__ = [
    "tool_descriptions",
    "exec_description",
]


def tool_descriptions() -> dict[str, str]:
    return {
        "python_exec": exec_description(),
    }


def exec_description(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra_path: Optional[Path] = None,
) -> str:
    """Generate description for tool registration (used as tool.__doc__)."""
    return exec_doc(namespace, toolset, tool, infra_path)
