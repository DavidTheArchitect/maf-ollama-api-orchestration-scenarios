import unittest

from invocations_scenarios.output_formatting import agent_response_to_text, workflow_result_to_text
from invocations_scenarios.scenarios import SCENARIOS
from invocations_scenarios.workflows import make_group_chat_termination


class GroupChatTerminationTests(unittest.TestCase):
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
        class Msg:
            def __init__(self, text):
                self.role = "assistant"
                self.text = text

        stop = make_group_chat_termination(("final recommendation",), 5)
        # mid-cycle: never fires, even with the phrase present
        self.assertFalse(stop([Msg("FINAL RECOMMENDATION: approve")] * 3))
        # cycle end without the phrase: continues into cycle two
        self.assertFalse(stop([Msg("still debating")] * 5))
        # cycle end with the phrase in the closing message: fires
        self.assertTrue(stop([Msg("still debating")] * 4 + [Msg("FINAL RECOMMENDATION: approve")]))
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


class WorkflowFormattingTests(unittest.TestCase):
    def test_extracts_nested_message_text_without_object_repr(self):
        class NestedMessage:
            text = "Approve after validating rollback."

        class WrappedMessage:
            author_name = "ActionPlannerAgent"
            role = "assistant"
            text = ""
            contents = [NestedMessage()]

        class WrappedResponse:
            text = ""
            messages = [WrappedMessage()]

        text = agent_response_to_text(WrappedResponse())

        self.assertIn("ActionPlannerAgent", text)
        self.assertIn("Approve after validating rollback.", text)
        self.assertNotIn(" object at 0x", text)

    def test_uses_intermediate_outputs_for_framework_termination_marker(self):
        class FakeEvents:
            def get_outputs(self):
                return ["Workflow terminated due to reaching maximum reset count."]

            def get_intermediate_outputs(self):
                return ["Useful specialist analysis."]

        self.assertEqual(workflow_result_to_text(FakeEvents()), "Useful specialist analysis.")


if __name__ == "__main__":
    unittest.main()
