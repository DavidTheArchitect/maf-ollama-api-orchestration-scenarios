import unittest

from review_bot.workflows import _agent_response_to_text


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

        text = _agent_response_to_text(WrappedResponse())

        self.assertIn("ActionPlannerAgent", text)
        self.assertIn("Approve after validating rollback.", text)
        self.assertNotIn(" object at 0x", text)


if __name__ == "__main__":
    unittest.main()
