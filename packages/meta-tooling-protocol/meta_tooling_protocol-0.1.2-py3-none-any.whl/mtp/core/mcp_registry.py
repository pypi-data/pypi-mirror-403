"""
Registry client for MCP servers.
"""

from __future__ import annotations

from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "MCP_REGISTRY_BASE",
    "InputDef",
    "TransportDef",
    "PackageDef",
    "RemoteDef",
    "ServerDef",
    "ServerRef",
    "ServerSearchItem",
    "fetch_servers",
    "fetch_server",
]

MCP_REGISTRY_BASE = "https://registry.modelcontextprotocol.io/v0.1"


class InputDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    value: str | None = None
    isRequired: bool = False


class TransportDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    url: str | None = None
    headers: list[InputDef] = Field(default_factory=list)


class PackageDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    registryType: str | None = None
    identifier: str | None = None
    runtimeHint: str | None = None
    runtimeArguments: list[InputDef] = Field(default_factory=list)
    packageArguments: list[InputDef] = Field(default_factory=list)
    environmentVariables: list[InputDef] = Field(default_factory=list)
    transport: TransportDef | None = None


class RemoteDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    url: str | None = None
    headers: list[InputDef] = Field(default_factory=list)


class ServerDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    version: str | None = None
    description: str | None = None
    packages: list[PackageDef] = Field(default_factory=list)
    remotes: list[RemoteDef] = Field(default_factory=list)


class ServerRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str


class ServerSearchItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    server: ServerRef


class ServersResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    servers: list[ServerSearchItem] = Field(default_factory=list)


class ServerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    server: ServerDef | None = None


def fetch_servers(
    *,
    search: str,
    version: str = "latest",
    registry_base: str = MCP_REGISTRY_BASE,
) -> list[ServerSearchItem]:
    url = f"{registry_base}/servers"
    response = httpx.get(url, params={"search": search, "version": version}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return ServersResponse.model_validate(payload).servers


def fetch_server(
    *,
    server_name: str,
    version: str = "latest",
    registry_base: str = MCP_REGISTRY_BASE,
) -> ServerDef:
    encoded = quote(server_name, safe="")
    url = f"{registry_base}/servers/{encoded}/versions/{version}"
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    server = ServerResponse.model_validate(payload).server
    if server is None:
        raise RuntimeError("MCP registry returned empty server payload.")
    return server
