import json
import unittest
from importlib import import_module
from pathlib import Path

from release_room.notebook_helpers import agent_response_to_text, pattern_anatomy, responses_api_reference, workflow_result_to_text
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

    def test_patterns_are_complete_and_balanced(self):
        self.assertEqual(set(PATTERNS), {"sequential", "concurrent", "handoff", "group-chat", "magentic"})
        # Count by pattern dynamically rather than depending on a fixed total. Scenario
        # families are added in complete sets of five (one per pattern), so the patterns
        # stay balanced as the catalog grows.
        pattern_counts = {pattern: [scenario.pattern for scenario in SCENARIOS].count(pattern) for pattern in PATTERNS}
        self.assertEqual(len(set(pattern_counts.values())), 1, pattern_counts)
        self.assertEqual(len(SCENARIOS), sum(pattern_counts.values()))

    def test_scenario_16_quote_to_cash_family_present(self):
        ids = {scenario.id for scenario in SCENARIOS}
        for pattern in ("sequential", "concurrent", "handoff", "group-chat", "magentic"):
            self.assertIn(f"scenario-16-quote-to-cash-{pattern}", ids)

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

    def test_each_scenario_has_sample_payload(self):
        project_root = Path(__file__).resolve().parents[1]
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                sample_path = project_root / "samples" / f"{scenario.id}.json"
                payload = json.loads(sample_path.read_text(encoding="utf-8"))
                self.assertIsInstance(payload.get("input"), str)
                self.assertIsInstance(payload.get("stream"), bool)

    def test_extracts_nested_message_text_without_object_repr(self):
        class NestedMessage:
            text = "Approve after validating rollback."

        class WrappedMessage:
            author_name = "LaunchCoordinatorAgent"
            role = "assistant"
            text = ""
            contents = [NestedMessage()]

        class WrappedResponse:
            text = ""
            messages = [WrappedMessage()]

        text = agent_response_to_text(WrappedResponse())

        self.assertIn("LaunchCoordinatorAgent", text)
        self.assertIn("Approve after validating rollback.", text)
        self.assertNotIn(" object at 0x", text)

    def test_uses_intermediate_outputs_for_framework_termination_marker(self):
        class FakeEvents:
            def get_outputs(self):
                return ["The group chat has reached its termination condition."]

            def get_intermediate_outputs(self):
                return ["Useful launch council transcript."]

        self.assertEqual(workflow_result_to_text(FakeEvents()), "Useful launch council transcript.")


if __name__ == "__main__":
    unittest.main()
