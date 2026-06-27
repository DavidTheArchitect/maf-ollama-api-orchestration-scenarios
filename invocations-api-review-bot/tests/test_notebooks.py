import ast
import json
import unittest
from pathlib import Path

from review_bot.scenarios import SCENARIOS, SCENARIOS_BY_ID


def _scenario_uses_mcp(scenario):
    return any(agent.mcp_tools for agent in scenario.agents)


class NotebookCompanionTests(unittest.TestCase):
    def test_each_scenario_notebook_compiles(self):
        project_root = Path(__file__).resolve().parents[1]
        notebooks = sorted((project_root / "notebooks").glob("*.ipynb"))
        self.assertEqual(len(notebooks), len(SCENARIOS))

        seen: set[str] = set()
        for path in notebooks:
            with self.subTest(notebook=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                source_text = "\n".join("".join(cell.get("source", [])) for cell in data.get("cells", []))
                scenario_ids = [scenario.id for scenario in SCENARIOS if scenario.id in source_text]
                self.assertEqual(len(scenario_ids), 1)
                seen.add(scenario_ids[0])
                self.assertIn("review_bot.notebook_helpers", source_text)
                self.assertIn("review_bot.diagram_helpers", source_text)
                self.assertIn("Pattern Anatomy", source_text)
                self.assertIn("Flow Diagram", source_text)
                self.assertIn("display_scenario_flow", source_text)

                if _scenario_uses_mcp(SCENARIOS_BY_ID[scenario_ids[0]]):
                    self.assertIn("MCP Tool Context", source_text)
                    self.assertIn("review_bot.mcp_servers", source_text)
                    self.assertIn("mcp_tool_context", source_text)

                for index, cell in enumerate(data.get("cells", [])):
                    self.assertIsNone(cell.get("execution_count"))
                    self.assertFalse(cell.get("outputs"))
                    if cell.get("cell_type") == "code":
                        source = "".join(cell.get("source", []))
                        compile(source, f"{path}#cell{index}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

        self.assertEqual(seen, {scenario.id for scenario in SCENARIOS})


if __name__ == "__main__":
    unittest.main()
