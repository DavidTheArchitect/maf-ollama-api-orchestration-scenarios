import unittest

from review_bot.code_tools import (
    AVAILABLE_CODE_TOOLS,
    compose_summary,
    effective_code_tools,
    extract_action_items,
    make_checklist,
    note_observation,
    rate_risk,
    resolve_code_tools,
    tally_votes,
)
from review_bot.scenarios import SCENARIOS


class CodeToolTests(unittest.TestCase):
    def test_note_observation_normalizes(self):
        self.assertEqual(note_observation("Risk", "  rollback gap "), "[risk] rollback gap")

    def test_rate_risk_clamps_and_tiers(self):
        result = rate_risk(9, -2)
        self.assertEqual(result["impact"], 5)
        self.assertEqual(result["likelihood"], 1)
        self.assertEqual(result["score"], 5)
        self.assertIn(result["tier"], {"low", "medium", "high", "critical"})

    def test_make_checklist(self):
        self.assertEqual(make_checklist(["a", "", "b"]).count("- [ ]"), 2)

    def test_extract_action_items_dedupes_and_limits(self):
        items = extract_action_items("Do X. Do X; Do Y\nDo Z")
        self.assertEqual(items[:3], ["Do X", "Do Y", "Do Z"])
        self.assertLessEqual(len(items), 8)

    def test_tally_votes(self):
        self.assertEqual(tally_votes(["approve", "yes", "reject"])["decision"], "approved")
        self.assertEqual(tally_votes(["no-go", "block"])["decision"], "rejected")

    def test_compose_summary(self):
        out = compose_summary({"Scope": "x", "Risk": "y"})
        self.assertIn("## Scope", out)
        self.assertIn("## Risk", out)

    def test_resolve_rejects_unknown(self):
        with self.assertRaises(ValueError):
            resolve_code_tools(["not_a_tool"])


class CodedAgentGuaranteeTests(unittest.TestCase):
    def test_every_agent_is_coded(self):
        for scenario in SCENARIOS:
            for agent in scenario.agents:
                with self.subTest(scenario=scenario.id, agent=agent.name):
                    tools = effective_code_tools(agent)
                    self.assertTrue(tools, "agent has no code tools (would be prompt-only)")
                    for tool in tools:
                        self.assertIn(tool, AVAILABLE_CODE_TOOLS)


if __name__ == "__main__":
    unittest.main()
