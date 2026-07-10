import json
import unittest
from importlib import import_module
from pathlib import Path

from responses_scenarios.notebook_helpers import agent_response_to_text, pattern_anatomy, responses_api_reference, workflow_result_to_text
from responses_scenarios.scenarios import PATTERNS, SCENARIOS, normalize_scenario_id
from responses_scenarios.workflows import normalize_workflow_name


def _expected_max_tokens(scenario) -> int:
    if scenario.pattern in {"group-chat", "magentic"}:
        return 1500
    if scenario.id.startswith("scenario-16-") or scenario.id == "scenario-18-agent-framework-primitives":
        return 1500
    return 1000


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

    def test_patterns_are_complete_with_expected_counts(self):
        self.assertEqual(set(PATTERNS), {"sequential", "concurrent", "handoff", "group-chat", "magentic"})
        # Scenario families 01-16 land in complete sets of five (one per pattern).
        # Scenario 17 adds a fifth group chat on purpose: it teaches the A2A
        # protocol, and group chat is the pattern where a remote peer seat is
        # most instructive. Scenario 18 adds a fifth sequential scenario as a
        # primitive lab because sequential is the least surprising runtime shell.
        pattern_counts = {pattern: [scenario.pattern for scenario in SCENARIOS].count(pattern) for pattern in PATTERNS}
        self.assertEqual(
            pattern_counts,
            {"sequential": 6, "concurrent": 5, "handoff": 5, "group-chat": 6, "magentic": 5},
        )
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

    def test_each_scenario_has_recommended_token_budget(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                self.assertIn(scenario.max_tokens, {1000, 1500})
                self.assertEqual(scenario.max_tokens, _expected_max_tokens(scenario))

    def test_each_scenario_has_companion_module(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                module_name = scenario.id.replace("-", "_")
                module = import_module(f"responses_scenarios.scenarios.{module_name}")
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
                self.assertIn(f"--max-tokens {scenario.max_tokens}", reference["server_command"])

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

    def test_handoff_specialists_declare_curated_route_keywords(self):
        """Every routable handoff specialist has explicit lowercase keywords."""

        for scenario in SCENARIOS:
            if scenario.pattern != "handoff":
                continue
            for agent in scenario.agents[1:]:
                if agent.name == scenario.handoff_finisher:
                    continue
                with self.subTest(scenario=scenario.id, agent=agent.name):
                    self.assertTrue(agent.route_keywords)
                    for keyword in agent.route_keywords:
                        self.assertEqual(keyword, keyword.lower())

    def test_group_chat_termination_only_fires_at_cycle_end(self):
        from responses_scenarios.workflows import make_group_chat_termination

        class Msg:
            def __init__(self, text):
                self.role = "assistant"
                self.text = text

        stop = make_group_chat_termination(("final recommendation",), 5)
        # mid-cycle: never fires, even with the phrase present
        self.assertFalse(stop([Msg("FINAL RECOMMENDATION: launch")] * 3))
        # cycle end without the phrase: continues into cycle two
        self.assertFalse(stop([Msg("still debating")] * 5))
        # cycle end with the phrase in the closing message: fires
        self.assertTrue(stop([Msg("still debating")] * 4 + [Msg("FINAL RECOMMENDATION: launch")]))
        # hard cap after two full cycles regardless of phrases
        self.assertTrue(stop([Msg("still debating")] * 10))

    def test_group_chat_scenarios_declare_termination_phrases(self):
        for scenario in SCENARIOS:
            if scenario.pattern != "group-chat":
                continue
            with self.subTest(scenario=scenario.id):
                self.assertTrue(scenario.termination_phrases)
                closing = scenario.agents[-1]
                joined = closing.instructions.lower()
                for phrase in scenario.termination_phrases:
                    self.assertIn(phrase.rstrip(":"), joined)

    def test_uses_intermediate_outputs_for_framework_termination_marker(self):
        class FakeEvents:
            def get_outputs(self):
                return ["The group chat has reached its termination condition."]

            def get_intermediate_outputs(self):
                return ["Useful launch council transcript."]

        self.assertEqual(workflow_result_to_text(FakeEvents()), "Useful launch council transcript.")


if __name__ == "__main__":
    unittest.main()
