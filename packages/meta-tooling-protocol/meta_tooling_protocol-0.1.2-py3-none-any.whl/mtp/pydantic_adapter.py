"""
Pydantic adapter for MTP.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .core.io import BlockingInput, BlockingOutput
from .core.runtime import Instance, ensure_instance
from .help import exec_description

__all__ = ["PydanticAdapter"]


def _execute(
    request: BlockingInput,
    instance: Optional[Instance],
) -> BlockingOutput:
    active = ensure_instance(instance)
    if request.notebook_path:
        active.set_notebook_path(request.notebook_path)
    return active.exec(
        code=request.code,
    )


class PydanticAdapter:
    """Expose MTP as a Pydantic-compatible function tool."""

    def __init__(
        self,
        instance: Optional[Instance] = None,
        *,
        namespace: str | None = None,
        toolset: str | None = None,
        tool: str | None = None,
        infra_path: Optional[Path] = None,
    ) -> None:
        self._instance = instance
        self._namespace = namespace
        self._toolset = toolset
        self._tool = tool
        self._infra_path = infra_path

    def tool(self) -> Callable[[BlockingInput], BlockingOutput]:
        def _tool(request: BlockingInput) -> BlockingOutput:
            return _execute(request, self._instance)

        _tool.__name__ = "python_exec"
        _tool.__doc__ = exec_description(
            namespace=self._namespace,
            toolset=self._toolset,
            tool=self._tool,
            infra_path=self._infra_path,
        )
        return _tool
