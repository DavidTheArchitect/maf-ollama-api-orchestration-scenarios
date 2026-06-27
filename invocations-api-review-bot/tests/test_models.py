import unittest

from review_bot.models import RequestValidationError, build_review_prompt, parse_review_request
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

    def test_has_all_five_patterns(self):
        self.assertEqual(set(PATTERNS), {"sequential", "concurrent", "handoff", "group-chat", "magentic"})
        self.assertEqual(len(SCENARIOS), 5)

    def test_each_scenario_has_four_to_eight_agents(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario.id):
                self.assertGreaterEqual(len(scenario.agents), 4)
                self.assertLessEqual(len(scenario.agents), 8)
                names = [agent.name for agent in scenario.agents]
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(scenario.learning_goal)
                self.assertTrue(scenario.when_to_use)


if __name__ == "__main__":
    unittest.main()
