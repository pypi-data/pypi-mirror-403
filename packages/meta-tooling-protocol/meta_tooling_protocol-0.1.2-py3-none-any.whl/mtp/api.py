"""
FastAPI adapter for MTP.
"""

from __future__ import annotations

from typing import Optional

from .core.io import BlockingInput, BlockingOutput
from .core.runtime import Instance
from .help import exec_description

__all__ = ["APIAdapter"]


def _execute(
    request: BlockingInput,
    instance: Optional[Instance],
) -> BlockingOutput:
    if instance is None:
        instance = Instance()
    if request.notebook_path:
        instance.set_notebook_path(request.notebook_path)
    return instance.exec(
        code=request.code,
    )


class APIAdapter:
    """Expose MTP as a FastAPI application."""

    def __init__(
        self,
        instance: Optional[Instance] = None,
    ) -> None:
        self._instances: dict[str, Instance] = {}
        if instance is not None:
            self._instances["default"] = instance

    def app(self, *, path: str = ""):
        from fastapi import FastAPI

        app = FastAPI(title="mtp", description=exec_description())

        def _get_instance(instance_id: str, *, notebook_path: Optional[str] = None) -> Instance:
            instance = self._instances.get(instance_id)
            if instance is None:
                instance = Instance(notebook_path=notebook_path)
                self._instances[instance_id] = instance
            elif notebook_path:
                instance.set_notebook_path(notebook_path)
            return instance

        @app.post(
            f"{path}/python_exec",
            response_model=BlockingOutput,
            operation_id="python_exec",
            description=exec_description(),
            responses={
                200: {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "example": BlockingOutput(
                                stdout="",
                                stderr="",
                                result={"ok": True},
                                traceback=None,
                            ).model_dump()
                        }
                    },
                }
            },
        )
        async def python_exec_mtp(request: BlockingInput) -> BlockingOutput:
            instance_id = request.instance_id or "default"
            instance = _get_instance(instance_id, notebook_path=request.notebook_path)
            return _execute(request, instance)

        return app
