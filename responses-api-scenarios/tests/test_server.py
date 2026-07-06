"""Offline tests for the server entry-point helpers."""

import unittest

from release_room.server import _run_with_optional_port, build_parser


class RunDispatchTests(unittest.TestCase):
    def test_passes_port_when_signature_accepts_it(self):
        calls = []

        class Host:
            def run(self, port=None):
                calls.append(port)

        _run_with_optional_port(Host(), 8088)
        self.assertEqual(calls, [8088])

    def test_falls_back_when_signature_rejects_port(self):
        calls = []

        class Host:
            def run(self):
                calls.append("no-port")

        _run_with_optional_port(Host(), 8088)
        self.assertEqual(calls, ["no-port"])

    def test_type_error_inside_run_propagates(self):
        class Host:
            def run(self, port=None):
                raise TypeError("bug inside the server")

        with self.assertRaisesRegex(TypeError, "bug inside the server"):
            _run_with_optional_port(Host(), 8088)


class ParserTests(unittest.TestCase):
    def test_parser_defaults_are_scenario_aware(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.scenario, "sequential-release-readiness")
        self.assertIsInstance(args.port, int)


if __name__ == "__main__":
    unittest.main()
