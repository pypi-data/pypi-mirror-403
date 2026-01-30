"""
Infra manager utilities (YAML-backed).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator
import yaml

__all__ = [
    "BaseInfraModel",
    "InfraConfig",
    "OpenApiInfra",
    "PythonInfra",
    "McpInfra",
    "CmdInfra",
    "CmdTool",
    "CmdToolEntry",
    "InfraItem",
    "InfraManager",
    "MTP_ROOT",
    "REGISTRY_PATH_DEFAULT",
    "load_infra",
    "save_infra",
]


# Module-level constants for paths
MTP_ROOT = Path.home() / ".mtp"
REGISTRY_PATH_DEFAULT = MTP_ROOT / "infra.yaml"


class BaseInfraModel(BaseModel):
    """Base model for all infra-related models with common config.

    Users can inherit from this class to create custom infra types.
    """
    model_config = ConfigDict(extra="forbid")


class InfraConfig(BaseInfraModel):
    default_generator: str = "openapi"


class OpenApiInfra(BaseInfraModel):
    type: Literal["openapi", "grpc"]
    name: str
    source: str
    generator: str | None = None


class PythonInfra(BaseInfraModel):
    type: Literal["python"]
    name: str
    path: str
    module: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class McpInfra(BaseInfraModel):
    type: Literal["mcp"]
    name: str
    transport: str
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    server: str | None = None
    version: str | None = None
    description: str | None = None
    registry_type: str | None = None
    package: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CmdTool(BaseInfraModel):
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    shell: bool = False
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CmdInfra(BaseInfraModel):

    type: Literal["cmd"]
    name: str
    tools: list[CmdTool] = Field(default_factory=list)
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    shell: bool = False
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_tools(self) -> "CmdInfra":
        if self.tools:
            return self
        if not self.command:
            raise ValueError("cmd infra requires tools or command")
        self.tools = [
            CmdTool(
                name=self.name,
                command=self.command,
                args=self.args,
                cwd=self.cwd,
                env=self.env,
                shell=self.shell,
                description=self.description,
                metadata=self.metadata,
            )
        ]
        return self


class CmdToolEntry(BaseInfraModel):
    namespace: str
    toolset: str
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    shell: bool = False
    description: str | None = None

    @classmethod
    def from_infra(cls, infra: CmdInfra, tool: CmdTool) -> "CmdToolEntry":
        return cls(
            namespace=infra.name,
            toolset=infra.name,
            name=tool.name,
            command=tool.command,
            args=tool.args,
            cwd=tool.cwd,
            env=tool.env,
            shell=tool.shell,
            description=tool.description,
        )


InfraItem = Annotated[Union[OpenApiInfra, PythonInfra, McpInfra, CmdInfra], Field(discriminator="type")]


class InfraManager(BaseInfraModel):
    config: InfraConfig = Field(default_factory=InfraConfig)
    dependency: list[str] = Field(default_factory=list)
    infras: list[InfraItem] = Field(default_factory=list)

    def get(self, name: str) -> InfraItem | None:
        """Get infra item by name."""
        return next((item for item in self.infras if item.name == name), None)

    def upsert(self, item: InfraItem) -> None:
        """Insert or update infra item."""
        for idx, current in enumerate(self.infras):
            if current.name == item.name:
                self.infras[idx] = item
                return
        self.infras.append(item)

    def remove(self, name: str) -> None:
        """Remove infra item by name."""
        self.infras = [item for item in self.infras if item.name != name]

    @property
    def sdks(self) -> list[OpenApiInfra]:
        """Get all OpenAPI/gRPC SDK infras."""
        return [item for item in self.infras if isinstance(item, OpenApiInfra)]

    @property
    def python(self) -> list[PythonInfra]:
        """Get all Python infras."""
        return [item for item in self.infras if isinstance(item, PythonInfra)]

    @property
    def mcps(self) -> list[McpInfra]:
        """Get all MCP infras."""
        return [item for item in self.infras if isinstance(item, McpInfra)]

    @property
    def cmd(self) -> list[CmdInfra]:
        """Get all command-line tool infras."""
        return [item for item in self.infras if isinstance(item, CmdInfra)]

    def cmd_entries(self) -> list[CmdToolEntry]:
        """Get all command-line tool entries."""
        return [
            CmdToolEntry.from_infra(infra, tool)
            for infra in self.cmd
            for tool in infra.tools
        ]


def load_infra(path: Path | None = None) -> InfraManager:
    """Load infra manager from YAML file.

    Args:
        path: Path to infra.yaml file. Defaults to ~/.mtp/infra.yaml

    Returns:
        InfraManager instance
    """
    path = path or REGISTRY_PATH_DEFAULT
    if not path.exists():
        return InfraManager()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return InfraManager.model_validate(data)


def save_infra(manager: InfraManager, path: Path | None = None) -> None:
    """Save infra manager to YAML file.

    Args:
        manager: InfraManager instance to save
        path: Path to infra.yaml file. Defaults to ~/.mtp/infra.yaml
    """
    path = path or REGISTRY_PATH_DEFAULT
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = manager.model_dump(exclude_none=True, exclude_defaults=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
