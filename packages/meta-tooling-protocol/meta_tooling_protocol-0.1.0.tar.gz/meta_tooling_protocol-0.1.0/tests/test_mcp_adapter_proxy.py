import asyncio
import inspect
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from mtp.core.mcp_client import ToolInfo
from mtp.core.registry import InfraManager, McpInfra, save_infra
from mtp.mcp_server import MCPAdapter


class DummyServer:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str, description: str = ""):
        def decorator(func):
            self.tools[name] = func
            return func

        return decorator


class McpAdapterProxyTests(TestCase):
    def test_registers_and_calls_proxy_tool(self) -> None:
        entry = McpInfra(
            type="mcp",
            name="github",
            transport="stdio",
            command="dummy",
        )
        infra = InfraManager(infras=[entry])

        with tempfile.TemporaryDirectory() as tmp_dir:
            infra_path = Path(tmp_dir) / "infra.yaml"
            save_infra(infra, infra_path)

            server = DummyServer()
            tool_info = ToolInfo(
                name="echo",
                description="Echo tool",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )

            with patch("mtp.mcp_server.list_tools_sync", return_value=[tool_info]), patch(
                "mtp.mcp_server.call_tool", new=AsyncMock(return_value={"ok": True})
            ) as mock_call:
                mtp = MCPAdapter(aggregate=False, infra_path=infra_path)
                mtp._register_mcp_tools(server, set())

                func = server.tools.get("github.echo")
                self.assertIsNotNone(func)
                sig = inspect.signature(func)
                self.assertIn("text", sig.parameters)
                self.assertFalse(
                    any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
                )

                result = asyncio.run(func(text="hi"))
                self.assertEqual(result, {"ok": True})
                mock_call.assert_called_once()
