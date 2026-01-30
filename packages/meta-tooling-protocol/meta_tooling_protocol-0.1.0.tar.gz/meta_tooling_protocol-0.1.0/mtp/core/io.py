"""
I/O models for MTP runtime.
"""

from __future__ import annotations

from typing import Optional, List
import traceback

from pydantic import BaseModel, ConfigDict, Field, JsonValue

__all__ = [
    "BlockingInput",
    "BlockingOutput",
    "InstanceStatus",
    "Traceback",
    "TracebackFrame",
]


class BlockingInput(BaseModel):
    """Tool input."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "result = {'ok': True}",
                    "timeout": 30,
                    "notebook_path": None,
                    "instance_id": "default",
                }
            ]
        }
    )

    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(30, description="Execution timeout (seconds)")
    notebook_path: Optional[str] = Field(
        None,
        description="Path to persist outputs as an .ipynb notebook",
    )
    instance_id: Optional[str] = Field(
        None,
        description="Instance id (defaults to 'default' when omitted)",
    )

    def __repr__(self) -> str:
        note = f", notebook={self.notebook_path}" if self.notebook_path else ""
        instance = f", instance={self.instance_id}" if self.instance_id else ""
        return f"Tool: MTP (timeout={self.timeout}s{note}{instance})\n\n{self.code}"


class TracebackFrame(BaseModel):
    """代表调用栈中的一层"""

    filename: str
    lineno: Optional[int]
    name: str
    line: Optional[str] = ""


class Traceback(BaseModel):
    """结构化的异常对象"""

    exc_type: str = Field(..., description="Exception type name, e.g. 'ValueError'")
    exc_value: str = Field(..., description="Exception message")
    frames: List[TracebackFrame] = Field(default_factory=list)

    @classmethod
    def from_exception(cls, exc: BaseException) -> "Traceback":
        tb = exc.__traceback__
        frames: List[TracebackFrame] = []
        if tb is not None:
            extracted = traceback.extract_tb(tb)
            frames = [
                TracebackFrame(
                    filename=frame.filename,
                    lineno=frame.lineno,
                    name=frame.name,
                    line=frame.line or "",
                )
                for frame in extracted
            ]
        return cls(
            exc_type=type(exc).__name__,
            exc_value=str(exc),
            frames=frames,
        )

    def to_string(self) -> str:
        """还原为标准的 Python traceback 字符串，用于打印"""
        lines = ["Traceback (most recent call last):"]
        for frame in self.frames:
            lines.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}')
            if frame.line:
                lines.append(f"    {frame.line.strip()}")
        lines.append(f"{self.exc_type}: {self.exc_value}")
        return "\n".join(lines)


class BlockingOutput(BaseModel):
    """Tool output."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "stdout": "",
                    "stderr": "",
                    "result": {"ok": True},
                    "traceback": None,
                }
            ]
        }
    )

    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    result: Optional[JsonValue] = Field(
        default=None,
        description="Value of result variable",
    )
    traceback: Optional[Traceback] = Field(None, description="Error traceback")

    def __repr__(self) -> str:
        if self.traceback:
            lines = []
            if self.stderr.strip():
                lines.append(f"[stderr]\n{self.stderr.strip()}")
            lines.append(f"\n[Traceback]\n{self.traceback.to_string()}")
            return "\n".join(lines)

        lines = []
        if self.stdout.strip():
            lines.append(f"[stdout]\n{self.stdout.strip()}")
        if self.stderr.strip():
            lines.append(f"[stderr]\n{self.stderr.strip()}")
        if self.result is not None:
            lines.append(f"[result]\n{self.result}")
        return "\n\n".join(lines) if lines else "(no output)"


class InstanceStatus(BaseModel):
    """Instance lifecycle status."""

    active: bool = Field(..., description="Whether an instance is active")
    message: str = Field(..., description="Status message")
    instance_id: Optional[str] = Field(None, description="Instance id")
