import unittest

from mtp.core.docgen import help_doc
from mtp.core.registry import CmdInfra, CmdTool, InfraManager, McpInfra


class DocgenFilterTests(unittest.TestCase):
    def test_help_doc_toolset_filters_scope(self) -> None:
        infra = InfraManager(
            infras=[
                CmdInfra(
                    type="cmd",
                    name="docgogo",
                    tools=[
                        CmdTool(
                            name="docgogo",
                            command="echo",
                            args=["ok"],
                            description="Gogo scanner",
                        )
                    ],
                ),
                CmdInfra(
                    type="cmd",
                    name="doccurl",
                    tools=[
                        CmdTool(
                            name="doccurl",
                            command="curl",
                            args=["-s"],
                            description="Curl client",
                        )
                    ],
                ),
                McpInfra(
                    type="mcp",
                    name="docmcp",
                    transport="stdio",
                    command="dummy",
                ),
            ]
        )

        content = help_doc(toolset="docgogo", infra=infra)
        self.assertIn("# infra", content)
        self.assertIn("## docgogo", content)
        self.assertIn("#### docgogo", content)
        self.assertNotIn("doccurl", content)
        self.assertNotIn("docmcp", content)
        self.assertNotIn("# mtp", content)
