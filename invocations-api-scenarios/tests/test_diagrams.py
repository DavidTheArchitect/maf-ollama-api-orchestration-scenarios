import unittest

from review_bot.diagram_helpers import scenario_flow_diagram
from review_bot.scenarios import SCENARIOS


PATTERN_MARKERS = {
    "sequential": ("stage 1",),
    "concurrent": ("Fan out", "Aggregate findings"),
    "handoff": ("Ownership decision", "handoff"),
    "group-chat": ("Round-robin selector", "Termination condition"),
    "magentic": ("Plan and delegate", "Progress ledger"),
}


class ScenarioDiagramTests(unittest.TestCase):
    def test_each_scenario_has_runtime_mermaid_diagram(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                diagram = scenario_flow_diagram(scenario)
                self.assertTrue(diagram.title)
                self.assertTrue(diagram.mermaid.startswith("flowchart TD"))
                self.assertTrue(diagram.image_url.startswith("https://mermaid.ink/img/"))
                self.assertIn("Invocations API /invocations", diagram.mermaid)
                self.assertIn("Build orchestration prompt", diagram.mermaid)
                self.assertIn(scenario.id, diagram.mermaid)
                self.assertIn(scenario.pattern, diagram.mermaid)
                for agent in scenario.agents:
                    self.assertIn(agent.name, diagram.mermaid)
                for marker in PATTERN_MARKERS[scenario.pattern]:
                    self.assertIn(marker, diagram.mermaid)

    def test_mcp_scenarios_show_dashed_tool_links(self):
        for scenario in SCENARIOS:
            declared_tools = {tool for agent in scenario.agents for tool in agent.mcp_tools}
            if not declared_tools:
                continue
            with self.subTest(scenario=scenario.id):
                mermaid = scenario_flow_diagram(scenario).mermaid
                self.assertIn("-.->|mcp tool|", mermaid)
                for tool in declared_tools:
                    self.assertIn(f"tool_{tool}", mermaid)

    def test_non_mcp_scenarios_have_no_tool_links(self):
        for scenario in SCENARIOS:
            if any(agent.mcp_tools for agent in scenario.agents):
                continue
            with self.subTest(scenario=scenario.id):
                self.assertNotIn("-.->|mcp tool|", scenario_flow_diagram(scenario).mermaid)


if __name__ == "__main__":
    unittest.main()
