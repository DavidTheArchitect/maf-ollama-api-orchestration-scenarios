import json
import unittest
from importlib import import_module
from pathlib import Path

from review_bot.models import RequestValidationError, build_review_prompt, parse_review_request
from review_bot.notebook_helpers import invocation_reference, pattern_anatomy
from review_bot.scenarios import PATTERNS, SCENARIOS


class ReviewRequestTests(unittest.TestCase):
    def test_parse_defaults_to_concurrent(self):
        request = parse_review_request({"task": "Review this change"})
        self.assertEqual(request.pattern, "concurrent")
        self.assertEqual(request.scenario, "concurrent-pr-review")
        self.assertEqual(request.subject, "unspecified subject")

    def test_parse_accepts_scenario(self):
        request = parse_review_request(
            {
                "scenario": "handoff-support-triage",
                "task": "Route this risk",
                "subject": "owner/repo",
                "artifacts": ["a.py"],
                "constraints": ["brief"],
            }
        )
        self.assertEqual(request.pattern, "handoff")
        self.assertEqual(request.artifacts, ["a.py"])

    def test_pattern_alias_maps_to_default_scenario(self):
        request = parse_review_request({"pattern": "magentic", "task": "Coordinate incident"})
        self.assertEqual(request.scenario, "magentic-incident-response")

    def test_rejects_missing_task(self):
        with self.assertRaises(RequestValidationError):
            parse_review_request({"subject": "owner/repo"})

    def test_rejects_invalid_pattern(self):
        with self.assertRaises(RequestValidationError):
            parse_review_request({"pattern": "unknown", "task": "Review"})

    def test_rejects_scenario_pattern_mismatch(self):
        with self.assertRaises(RequestValidationError):
            parse_review_request({"scenario": "handoff-support-triage", "pattern": "concurrent", "task": "Review"})

    def test_prompt_contains_core_fields(self):
        request = parse_review_request({"task": "Review", "subject": "owner/repo", "artifacts": ["a.py"]})
        prompt = build_review_prompt(request, ["assistant: prior summary"])
        self.assertIn("owner/repo", prompt)
        self.assertIn("a.py", prompt)
        self.assertIn("prior summary", prompt)

    def test_patterns_are_complete_with_expected_counts(self):
        self.assertEqual(set(PATTERNS), {"sequential", "concurrent", "handoff", "group-chat", "magentic"})
        # Scenario families 01-16 land in complete sets of five (one per pattern).
        # Scenario 17 adds a fifth group chat on purpose: it teaches the A2A
        # protocol, and group chat is the pattern where a remote peer seat is
        # most instructive. Update these counts deliberately when adding scenarios.
        pattern_counts = {pattern: [scenario.pattern for scenario in SCENARIOS].count(pattern) for pattern in PATTERNS}
        self.assertEqual(
            pattern_counts,
            {"sequential": 4, "concurrent": 4, "handoff": 4, "group-chat": 5, "magentic": 4},
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
                names = [agent.name for agent in scenario.agents]
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(scenario.learning_goal)
                self.assertTrue(scenario.when_to_use)

    def test_each_scenario_has_companion_module(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                module_name = scenario.id.replace("-", "_")
                module = import_module(f"review_bot.scenarios.{module_name}")
                self.assertIs(module.SCENARIO, scenario)

    def test_notebook_helpers_describe_each_pattern(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                anatomy = pattern_anatomy(scenario)
                self.assertIn("control_flow", anatomy)
                self.assertIn("best_when", anatomy)
                request = parse_review_request({"scenario": scenario.id, "task": scenario.sample_task})
                reference = invocation_reference(scenario, request)
                self.assertEqual(reference["scenario"], scenario.id)
                self.assertEqual(reference["pattern"], scenario.pattern)

    def test_each_scenario_has_valid_sample_payload(self):
        project_root = Path(__file__).resolve().parents[1]
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                sample_path = project_root / "samples" / f"{scenario.id}.json"
                payload = json.loads(sample_path.read_text(encoding="utf-8"))
                request = parse_review_request(payload)
                self.assertEqual(request.scenario, scenario.id)
                self.assertEqual(request.pattern, scenario.pattern)


if __name__ == "__main__":
    unittest.main()
