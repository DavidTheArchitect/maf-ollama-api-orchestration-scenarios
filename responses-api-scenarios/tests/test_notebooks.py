import ast
import json
import unittest
from pathlib import Path

from release_room.scenarios import SCENARIOS, SCENARIOS_BY_ID


def _scenario_uses_mcp(scenario):
    return any(agent.mcp_tools for agent in scenario.agents)


def _imports_package(source: str, package: str) -> bool:
    tree = ast.parse(source, mode="exec", type_comments=True)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == package or alias.name.startswith(f"{package}."):
                    return True
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == package or module.startswith(f"{package}."):
                return True
    return False


class NotebookCompanionTests(unittest.TestCase):
    def test_each_scenario_notebook_is_self_contained(self):
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
                self.assertNotIn("find_project_root", source_text)
                self.assertNotIn("sys.path", source_text)
                self.assertNotIn("release_room", source_text)
                self.assertIn("qwen3:14b", source_text)
                self.assertIn("_APTOS_STYLE", source_text)
                self.assertIn("Pattern Anatomy", source_text)
                self.assertIn("Flow Diagram", source_text)
                self.assertIn("display_scenario_flow", source_text)
                self.assertIn("apply_notebook_style", source_text)
                self.assertIn("agent_capability_map", source_text)
                self.assertIn("Instruction-Led LLM Agents", source_text)
                self.assertIn("make_agent", source_text)
                self.assertIn("build_workflow", source_text)
                self.assertNotIn("CODE_TOOLS", source_text)
                self.assertNotIn("effective_code_tools", source_text)
                self.assertNotIn("resolve_code_tools", source_text)
                self.assertNotIn("coded_agent_tool_map", source_text)

                if _scenario_uses_mcp(SCENARIOS_BY_ID[scenario_ids[0]]):
                    self.assertIn("MCP Tool Context", source_text)
                    self.assertIn("mcp_tool_context", source_text)

                for index, cell in enumerate(data.get("cells", [])):
                    self.assertIsNone(cell.get("execution_count"))
                    self.assertFalse(cell.get("outputs"))
                    if cell.get("cell_type") == "code":
                        source = "".join(cell.get("source", []))
                        compile(source, f"{path}#cell{index}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                        self.assertFalse(_imports_package(source, "release_room"))

        self.assertEqual(seen, {scenario.id for scenario in SCENARIOS})


if __name__ == "__main__":
    unittest.main()
