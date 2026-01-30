import asyncio
import inspect
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from mtp.core.mcp_client import ToolCallResult, list_tools_sync
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


class McpProxyTests(TestCase):
    def test_proxy_tool_async_call_in_event_loop(self) -> None:
        if shutil.which("npx") is None:
            self.skipTest("npx not available")
        entry = McpInfra(
            type="mcp",
            name="playwright",
            transport="stdio",
            command="npx",
            args=["playwright-wizard-mcp"],
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            infra_path = Path(tmp_dir) / "infra.yaml"
            registry = InfraManager(infras=[entry])
            save_infra(registry, infra_path)

            server = DummyServer()
            mtp = MCPAdapter(aggregate=True, infra_path=infra_path)
            mtp._register_mcp_tools(server, set())

            tools = [tool for tool in list_tools_sync(entry) if tool.name]
            self.assertTrue(tools)

            chosen_tool = None
            for item in tools:
                schema = item.input_schema or {}
                props = schema.get("properties") or {}
                required = schema.get("required") or []
                if not props and not required:
                    chosen_tool = item
                    break
            if chosen_tool is None:
                chosen_tool = tools[0]

            func = server.tools.get(f"playwright.{chosen_tool.name}")
            self.assertIsNotNone(func)
            sig = inspect.signature(func)
            self.assertFalse(
                any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
            )

            args: dict[str, object] = {}
            schema = chosen_tool.input_schema or {}
            required = set(schema.get("required") or [])
            props = schema.get("properties") or {}
            for name, prop in props.items():
                if name == "url":
                    args[name] = "https://www.baidu.com"
                elif prop.get("type") == "boolean":
                    args[name] = False
                elif prop.get("type") == "number":
                    args[name] = 0
                elif prop.get("type") == "array":
                    args[name] = []
                elif prop.get("type") == "object":
                    args[name] = {}
                else:
                    args[name] = "test"
            for name in required:
                if name not in args:
                    args[name] = "https://www.baidu.com"

            async def run():
                return await asyncio.wait_for(
                    func(**args),
                    timeout=120,
                )

            result = asyncio.run(run())
            self.assertIsInstance(result, ToolCallResult)
            self.assertFalse(result.is_error)
            self.assertTrue(result.content)
