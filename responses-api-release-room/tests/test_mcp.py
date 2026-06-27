import unittest

from release_room.agents import ENTERPRISE_MCP_MODULE, AgentSpec, build_enterprise_mcp_tool
from release_room.mcp_servers import enterprise_context
from release_room.scenarios import SCENARIOS

MCP_SCENARIO_IDS = {
    "sequential-procurement-approval",
    "concurrent-security-alert-enrichment",
    "handoff-claims-exception-routing",
    "group-chat-policy-exception-board",
    "magentic-business-continuity-drill",
}


class McpScenarioTests(unittest.TestCase):
    def test_expected_mcp_scenarios_use_mcp_tools(self):
        with_mcp = {
            scenario.id
            for scenario in SCENARIOS
            if any(agent.mcp_tools for agent in scenario.agents)
        }
        self.assertEqual(with_mcp, MCP_SCENARIO_IDS)

    def test_every_mcp_scenario_has_at_least_one_enabled_agent(self):
        for scenario in SCENARIOS:
            if scenario.id not in MCP_SCENARIO_IDS:
                continue
            with self.subTest(scenario=scenario.id):
                enabled = [agent for agent in scenario.agents if agent.mcp_tools]
                self.assertTrue(enabled, f"{scenario.id} has no MCP-enabled agent")

    def test_every_declared_tool_is_available_from_server(self):
        available = set(enterprise_context.list_tool_names())
        self.assertEqual(set(enterprise_context.AVAILABLE_TOOLS), available)
        for scenario in SCENARIOS:
            for agent in scenario.agents:
                for tool in agent.mcp_tools:
                    with self.subTest(scenario=scenario.id, agent=agent.name, tool=tool):
                        self.assertIn(tool, available)

    def test_non_mcp_scenarios_declare_no_tools(self):
        for scenario in SCENARIOS:
            if scenario.id in MCP_SCENARIO_IDS:
                continue
            with self.subTest(scenario=scenario.id):
                self.assertFalse(any(agent.mcp_tools for agent in scenario.agents))


class EnterpriseContextToolTests(unittest.TestCase):
    def test_lookup_known_and_unknown_records(self):
        found = enterprise_context.lookup_enterprise_record("VENDOR-4471")
        self.assertTrue(found["found"])
        self.assertEqual(found["name"], "Northwind Analytics")
        missing = enterprise_context.lookup_enterprise_record("NOPE")
        self.assertFalse(missing["found"])
        self.assertIn("VENDOR-4471", missing["known_ids"])

    def test_search_policy_is_deterministic(self):
        first = enterprise_context.search_policy("vendor security purchase")
        second = enterprise_context.search_policy("vendor security purchase")
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["match_count"], 1)

    def test_priority_score_clamps_and_tiers(self):
        result = enterprise_context.calculate_priority_score(99, -3, 2)
        self.assertEqual(result["impact"], 5)
        self.assertEqual(result["urgency"], 1)
        self.assertIn(result["tier"], {"low", "medium", "high", "critical"})

    def test_playbook_lookup(self):
        steps = enterprise_context.list_playbook_steps("procurement_approval")
        self.assertTrue(steps["found"])
        self.assertEqual(steps["step_count"], len(steps["steps"]))
        self.assertFalse(enterprise_context.list_playbook_steps("missing")["found"])

    def test_decision_log_is_deterministic_and_not_persisted(self):
        entry = enterprise_context.create_decision_log_entry("subject", "approve", "ok", "owner")
        again = enterprise_context.create_decision_log_entry("subject", "approve", "ok", "owner")
        self.assertEqual(entry["entry_id"], again["entry_id"])
        self.assertFalse(entry["persisted"])


class EnterpriseMcpToolBuildTests(unittest.TestCase):
    def test_build_tool_uses_local_module_and_restricts_tools(self):
        self.assertEqual(ENTERPRISE_MCP_MODULE, "release_room.mcp_servers.enterprise_context")
        spec = AgentSpec("ToolAgent", "x", "y", mcp_tools=("search_policy",))
        tool = build_enterprise_mcp_tool(spec)
        self.assertEqual(tool.approval_mode, "never_require")
        self.assertEqual(list(tool.allowed_tools), ["search_policy"])


if __name__ == "__main__":
    unittest.main()
