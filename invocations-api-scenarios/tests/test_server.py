"""Offline tests for the server entry-point and session-history helpers."""

import unittest

from review_bot.server import (
    _MAX_SESSIONS,
    _MAX_TURNS_PER_SESSION,
    _SESSION_TURNS,
    _openapi_spec,
    _record_turns,
    _run_with_optional_port,
    _session_history,
)


class RunDispatchTests(unittest.TestCase):
    def test_passes_port_when_signature_accepts_it(self):
        calls = []

        class Host:
            def run(self, port=None):
                calls.append(port)

        _run_with_optional_port(Host(), 8089)
        self.assertEqual(calls, [8089])

    def test_falls_back_when_signature_rejects_port(self):
        calls = []

        class Host:
            def run(self):
                calls.append("no-port")

        _run_with_optional_port(Host(), 8089)
        self.assertEqual(calls, ["no-port"])

    def test_type_error_inside_run_propagates(self):
        class Host:
            def run(self, port=None):
                raise TypeError("bug inside the server")

        with self.assertRaisesRegex(TypeError, "bug inside the server"):
            _run_with_optional_port(Host(), 8089)


class SessionHistoryTests(unittest.TestCase):
    def setUp(self):
        _SESSION_TURNS.clear()

    def tearDown(self):
        _SESSION_TURNS.clear()

    def test_turns_are_capped_per_session(self):
        for index in range(_MAX_TURNS_PER_SESSION):
            _record_turns("s1", f"task {index}", f"summary {index}")
        turns = _SESSION_TURNS["s1"]
        self.assertEqual(len(turns), _MAX_TURNS_PER_SESSION)
        self.assertIn(f"assistant: summary {_MAX_TURNS_PER_SESSION - 1}", turns[-1])

    def test_oldest_sessions_are_evicted(self):
        for index in range(_MAX_SESSIONS + 5):
            _session_history(f"session-{index}")
        self.assertLessEqual(len(_SESSION_TURNS), _MAX_SESSIONS)
        self.assertNotIn("session-0", _SESSION_TURNS)
        self.assertIn(f"session-{_MAX_SESSIONS + 4}", _SESSION_TURNS)

    def test_no_session_id_records_nothing(self):
        _record_turns(None, "task", "summary")
        self.assertEqual(_SESSION_TURNS, {})
        self.assertEqual(_session_history(None), [])


class OpenApiSpecTests(unittest.TestCase):
    def test_aliases_are_documented(self):
        properties = _openapi_spec()["paths"]["/invocations"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]["properties"]
        self.assertIn("repo", properties)
        self.assertIn("alias for 'subject'", properties["repo"]["description"].lower())
        self.assertIn("changed_files", properties)
        self.assertIn("alias for 'artifacts'", properties["changed_files"]["description"].lower())


if __name__ == "__main__":
    unittest.main()
