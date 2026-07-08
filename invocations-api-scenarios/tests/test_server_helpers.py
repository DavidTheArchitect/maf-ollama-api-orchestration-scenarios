import unittest

from invocations_scenarios.server import _chunk_text


class ServerHelperTests(unittest.TestCase):
    def test_chunk_text_preserves_content(self):
        text = "abcdefghijklmnopqrstuvwxyz"
        self.assertEqual("".join(_chunk_text(text, size=5)), text)

    def test_chunk_text_handles_empty_text(self):
        self.assertEqual(_chunk_text(""), [""])


if __name__ == "__main__":
    unittest.main()
