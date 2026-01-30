import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from mtp.core.registry import (
    CmdInfra,
    CmdTool,
    InfraManager,
    McpInfra,
    OpenApiInfra,
    PythonInfra,
    save_infra,
)


@contextmanager
def _infra_env(path: Path):
    prev = os.environ.get("MTP_INFRA")
    os.environ["MTP_INFRA"] = str(path)
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("MTP_INFRA", None)
        else:
            os.environ["MTP_INFRA"] = prev


def _clear_mtp_attr(name: str) -> None:
    import mtp

    if name in mtp.__dict__:
        del mtp.__dict__[name]


class InfraImportTests(TestCase):
    def test_cmd_import_and_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            infra_path = tmp_path / "infra.yaml"
            registry = InfraManager(
                infras=[
                    CmdInfra(
                        type="cmd",
                        name="hello_cmd",
                        tools=[
                            CmdTool(
                                name="hello_cmd",
                                command=sys.executable,
                                args=["-c", "print('ok')"],
                            )
                        ],
                    )
                ]
            )
            save_infra(registry, infra_path)

            with _infra_env(infra_path):
                _clear_mtp_attr("hello_cmd")
                from mtp import hello_cmd

                result = hello_cmd()
                self.assertEqual(result["returncode"], 0)
                self.assertIn("ok", result["stdout"])

    def test_python_import_toolset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            infra_path = tmp_path / "infra.yaml"
            tool_path = tmp_path / "mytools.py"
            tool_path.write_text(
                "\n".join(
                    [
                        "from mtp.core.docgen import namespace, toolset, tool",
                        "",
                        "namespace(\"mytools\")",
                        "",
                        "@toolset(\"math\")",
                        "class MathTools:",
                        "    @tool()",
                        "    def add(self, a: int, b: int) -> int:",
                        "        return a + b",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            registry = InfraManager(
                infras=[
                    PythonInfra(
                        type="python",
                        name="mytools",
                        path=str(tool_path),
                        module="mtp_dynamic.mytools_test",
                    )
                ]
            )
            save_infra(registry, infra_path)

            with _infra_env(infra_path):
                _clear_mtp_attr("mytools")
                sys.modules.pop("mtp_dynamic.mytools_test", None)
                from mtp import mytools

                self.assertEqual(mytools.math.add(a=1, b=2), 3)

    def test_sdk_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            infra_path = tmp_path / "infra.yaml"
            sdk_pkg = tmp_path / "sdks" / "cyberhub"
            sdk_pkg.mkdir(parents=True, exist_ok=True)
            (sdk_pkg / "__init__.py").write_text("NAME = 'cyberhub'\n", encoding="utf-8")

            registry = InfraManager(
                infras=[
                    OpenApiInfra(
                        type="openapi",
                        name="cyberhub",
                        source="https://example.com/openapi.json",
                    )
                ]
            )
            save_infra(registry, infra_path)

            with _infra_env(infra_path):
                _clear_mtp_attr("cyberhub")
                sys.modules.pop("cyberhub", None)
                from mtp import cyberhub

                self.assertEqual(cyberhub.NAME, "cyberhub")

    def test_mcp_import_proxy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            infra_path = tmp_path / "infra.yaml"
            registry = InfraManager(
                infras=[
                    McpInfra(
                        type="mcp",
                        name="github",
                        transport="stdio",
                        command="dummy",
                    )
                ]
            )
            save_infra(registry, infra_path)

            with _infra_env(infra_path):
                _clear_mtp_attr("github")
                with patch("mtp.core.mcp_client.call_tool_sync", return_value={"ok": True}) as mock_call:
                    from mtp import github

                    result = github.list_repos(owner="anthropics")
                    self.assertEqual(result, {"ok": True})
                    mock_call.assert_called_once()
