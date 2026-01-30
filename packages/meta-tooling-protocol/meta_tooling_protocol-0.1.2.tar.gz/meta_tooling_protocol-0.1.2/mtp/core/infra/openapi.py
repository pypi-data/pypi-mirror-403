"""
OpenAPI/gRPC infra helpers.
"""

from __future__ import annotations

from typing import Any

from ..docgen import (
    docs as _docs,
    list_namespaces as _list_namespaces,
    list_toolsets as _list_toolsets,
    list_tools as _list_tools,
)
from ..registry import InfraManager

__all__ = [
    "list_namespaces",
    "list_toolsets",
    "list_tools",
    "docs",
]


def list_namespaces(infra: InfraManager | None = None) -> list[str]:
    return _list_namespaces(generator="openapi", infra=infra)


def list_toolsets(namespace: str, infra: InfraManager | None = None) -> list[str]:
    return _list_toolsets(namespace, generator="openapi", infra=infra)


def list_tools(namespace: str, toolset: str, infra: InfraManager | None = None) -> list[str]:
    return _list_tools(namespace, toolset, generator="openapi", infra=infra)


def docs(
    namespace: str | None = None,
    toolset: str | None = None,
    tool: str | None = None,
    infra: InfraManager | None = None,
) -> str:
    return _docs(namespace=namespace, toolset=toolset, tool=tool, generator="openapi", infra=infra)
