import unittest

from review_bot.output_formatting import agent_response_to_text, workflow_result_to_text


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
