import unittest
from importlib import import_module

from release_room.notebook_helpers import pattern_anatomy, responses_api_reference
from release_room.scenarios import PATTERNS, SCENARIOS, normalize_scenario_id
from release_room.workflows import normalize_workflow_name


class WorkflowSelectionTests(unittest.TestCase):
    def test_normalizes_default_to_sequential(self):
        self.assertEqual(normalize_workflow_name(None), "sequential-release-readiness")

    def test_accepts_pattern_aliases(self):
        self.assertEqual(normalize_scenario_id("groupchat"), "group-chat-launch-council")
        self.assertEqual(normalize_scenario_id("group_chat"), "group-chat-launch-council")
        self.assertEqual(normalize_scenario_id("magentic"), "magentic-incident-response")

    def test_rejects_unknown_workflow(self):
        with self.assertRaises(ValueError):
            normalize_workflow_name("unknown")

    def test_has_all_five_patterns(self):
        self.assertEqual(set(PATTERNS), {"sequential", "concurrent", "handoff", "group-chat", "magentic"})
        self.assertEqual(len(SCENARIOS), 5)

    def test_each_scenario_has_four_to_eight_agents(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                self.assertGreaterEqual(len(scenario.agents), 4)
                self.assertLessEqual(len(scenario.agents), 8)
                names = [spec.name for spec in scenario.agents]
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(scenario.learning_goal)
                self.assertTrue(scenario.when_to_use)
                self.assertTrue(all(spec.instructions for spec in scenario.agents))

    def test_each_scenario_has_companion_module(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                module_name = scenario.id.replace("-", "_")
                module = import_module(f"release_room.scenarios.{module_name}")
                self.assertIs(module.SCENARIO, scenario)

    def test_notebook_helpers_describe_each_pattern(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                anatomy = pattern_anatomy(scenario)
                self.assertIn("control_flow", anatomy)
                self.assertIn("best_when", anatomy)
                reference = responses_api_reference(scenario)
                self.assertEqual(reference["payload"]["input"], scenario.sample_input)
                self.assertIn(scenario.id, reference["server_command"])


if __name__ == "__main__":
    unittest.main()
