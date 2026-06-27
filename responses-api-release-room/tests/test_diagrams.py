import unittest

from release_room.diagram_helpers import scenario_flow_diagram
from release_room.scenarios import SCENARIOS


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
                self.assertIn("Responses API /responses", diagram.mermaid)
                self.assertIn(scenario.id, diagram.mermaid)
                self.assertIn(scenario.pattern, diagram.mermaid)
                for agent in scenario.agents:
                    self.assertIn(agent.name, diagram.mermaid)
                for marker in PATTERN_MARKERS[scenario.pattern]:
                    self.assertIn(marker, diagram.mermaid)


if __name__ == "__main__":
    unittest.main()
