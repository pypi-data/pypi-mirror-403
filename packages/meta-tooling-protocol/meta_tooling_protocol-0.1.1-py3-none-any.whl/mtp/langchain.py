"""
LangChain adapter for MTP.
"""

from __future__ import annotations

from typing import Optional

from .core.io import BlockingInput, BlockingOutput
from .core.runtime import Instance, ensure_instance
from .help import exec_description, tool_descriptions

__all__ = ["LangchainAdapter"]


def _execute(
    request: BlockingInput,
    instance: Optional[Instance],
) -> BlockingOutput:
    active = ensure_instance(instance)
    return active.exec(
        code=request.code,
    )


class LangchainAdapter:
    """Expose MTP as a LangChain structured tool."""

    def __init__(
        self,
        instance: Optional[Instance] = None,
    ) -> None:
        self._instance = instance

    def tool(
        self,
        *,
        name: str = "python_exec",
        description: str = "Execute Python code and return result",
    ):
        from langchain_core.tools import StructuredTool

        def _tool(
            code: str,
            timeout: int = 30,
            notebook_path: Optional[str] = None,
        ) -> BlockingOutput:
            return _execute(
                BlockingInput(code=code, timeout=timeout, notebook_path=notebook_path),
                self._instance,
            )

        return StructuredTool.from_function(
            func=_tool,
            name=name,
            description=f"{tool_descriptions().get('python_exec', description)}\n\n{exec_description()}",
            args_schema=BlockingInput,
        )
