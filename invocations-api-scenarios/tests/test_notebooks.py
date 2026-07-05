import ast
import json
import unittest
from pathlib import Path

from review_bot.scenarios import SCENARIOS, SCENARIOS_BY_ID


def _scenario_uses_mcp(scenario):
    return any(agent.mcp_tools for agent in scenario.agents)


#: One marker unique to each pattern's orchestration machinery. Notebooks must
#: contain their own pattern's marker and none of the other patterns'.
_PATTERN_MACHINERY_MARKERS = {
    "sequential": "StageGateExecutor",
    "concurrent": "ConcurrentAggregatorExecutor",
    "handoff": "HandoffRouterExecutor",
    "group-chat": "GroupChatBuilder",
    "magentic": "MagenticBuilder",
}


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
                self.assertNotIn("review_bot", source_text)
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

                scenario = SCENARIOS_BY_ID[scenario_ids[0]]
                if _scenario_uses_mcp(scenario):
                    self.assertIn("MCP Tool Context", source_text)
                    self.assertIn("mcp_tool_context", source_text)

                # Cell-per-concept layout: enough cells, only this pattern's
                # machinery, an offline demo, and the styled transcript render.
                minimum_cells = 18 if _scenario_uses_mcp(scenario) else 15
                if any(getattr(spec, "a2a_url", None) for spec in scenario.agents):
                    minimum_cells = 20
                    self.assertIn("A2A Partner Context", source_text)
                    self.assertIn("agent-card.json", source_text)
                    self.assertIn("A2AAgent", source_text)
                self.assertGreaterEqual(len(data.get("cells", [])), minimum_cells)
                self.assertIn(_PATTERN_MACHINERY_MARKERS[scenario.pattern], source_text)
                for other_pattern, marker in _PATTERN_MACHINERY_MARKERS.items():
                    if other_pattern != scenario.pattern:
                        self.assertNotIn(marker, source_text)
                self.assertIn("# Demo (offline)", source_text)
                self.assertIn("render_transcript", source_text)
                self.assertIn("render_roster", source_text)

                for index, cell in enumerate(data.get("cells", [])):
                    self.assertIsNone(cell.get("execution_count"))
                    self.assertFalse(cell.get("outputs"))
                    if cell.get("cell_type") == "code":
                        source = "".join(cell.get("source", []))
                        compile(source, f"{path}#cell{index}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                        self.assertFalse(_imports_package(source, "review_bot"))

        self.assertEqual(seen, {scenario.id for scenario in SCENARIOS})


if __name__ == "__main__":
    unittest.main()
