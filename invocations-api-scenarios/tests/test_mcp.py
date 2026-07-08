import unittest

from invocations_scenarios.agents import (
    ENTERPRISE_MCP_MODULE,
    MCP_SERVER_MODULES,
    QUOTE_TO_CASH_MCP_MODULE,
    AgentSpec,
    build_mcp_tool,
)
from invocations_scenarios.mcp_servers import enterprise_context, quote_to_cash_context
from invocations_scenarios.scenarios import SCENARIOS

SERVERS = {
    "enterprise_context": enterprise_context,
    "quote_to_cash_context": quote_to_cash_context,
}

ENTERPRISE_MCP_SCENARIOS = {
    "sequential-procurement-approval",
    "concurrent-security-alert-enrichment",
    "handoff-claims-exception-routing",
    "group-chat-policy-exception-board",
    "magentic-business-continuity-drill",
}

QUOTE_TO_CASH_SCENARIOS = {
    "scenario-16-quote-to-cash-sequential",
    "scenario-16-quote-to-cash-concurrent",
    "scenario-16-quote-to-cash-handoff",
    "scenario-16-quote-to-cash-group-chat",
    "scenario-16-quote-to-cash-magentic",
}


class McpScenarioTests(unittest.TestCase):
    def test_server_available_tools_match_live_registry(self):
        for name, module in SERVERS.items():
            with self.subTest(server=name):
                self.assertEqual(set(module.AVAILABLE_TOOLS), set(module.list_tool_names()))

    def test_every_mcp_scenario_has_at_least_one_enabled_agent(self):
        for scenario in SCENARIOS:
            if not any(agent.mcp_tools for agent in scenario.agents):
                continue
            with self.subTest(scenario=scenario.id):
                self.assertTrue([a for a in scenario.agents if a.mcp_tools])

    def test_every_declared_tool_is_available_from_its_server(self):
        for scenario in SCENARIOS:
            for agent in scenario.agents:
                if not agent.mcp_tools:
                    continue
                with self.subTest(scenario=scenario.id, agent=agent.name):
                    self.assertIn(agent.mcp_server, SERVERS)
                    available = set(SERVERS[agent.mcp_server].AVAILABLE_TOOLS)
                    for tool in agent.mcp_tools:
                        self.assertIn(tool, available)

    def test_known_families_use_mcp(self):
        with_mcp = {s.id for s in SCENARIOS if any(a.mcp_tools for a in s.agents)}
        self.assertTrue(ENTERPRISE_MCP_SCENARIOS <= with_mcp)
        self.assertTrue(QUOTE_TO_CASH_SCENARIOS <= with_mcp)

    def test_instruction_tool_mentions_are_granted(self):
        """Any tool an agent's instructions name must be in its mcp_tools grant."""

        all_tools = set()
        for module in SERVERS.values():
            all_tools |= set(module.AVAILABLE_TOOLS)
        for scenario in SCENARIOS:
            for agent in scenario.agents:
                mentioned = {tool for tool in all_tools if tool in agent.instructions}
                with self.subTest(scenario=scenario.id, agent=agent.name):
                    self.assertLessEqual(
                        mentioned, set(agent.mcp_tools), mentioned - set(agent.mcp_tools)
                    )

    def test_sample_inputs_reference_known_fixture_ids(self):
        """Fixture-style IDs in MCP scenario samples must exist on their server."""

        import re as _re

        known = {
            "enterprise_context": set(enterprise_context._ENTERPRISE_RECORDS)
            | {policy["id"] for policy in enterprise_context._POLICY_CATALOG},
            "quote_to_cash_context": set(quote_to_cash_context._QUOTE_TRIGGERS)
            | set(quote_to_cash_context._CUSTOMER_PROFILES)
            | {entry["sku"] for entry in quote_to_cash_context._CATALOG},
        }
        id_pattern = _re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+\b")
        for scenario in SCENARIOS:
            servers = {a.mcp_server for a in scenario.agents if a.mcp_tools}
            if len(servers) != 1:
                continue
            valid = known[next(iter(servers))]
            for token in id_pattern.findall(scenario.sample_task):
                with self.subTest(scenario=scenario.id, token=token):
                    self.assertIn(token, valid)

    def test_quote_to_cash_scenarios_use_quote_server(self):
        for scenario in SCENARIOS:
            if scenario.id not in QUOTE_TO_CASH_SCENARIOS:
                continue
            with self.subTest(scenario=scenario.id):
                self.assertTrue(scenario.agents)
                for agent in scenario.agents:
                    self.assertEqual(agent.mcp_server, "quote_to_cash_context")
                    self.assertTrue(agent.mcp_tools)


class EnterpriseContextToolTests(unittest.TestCase):
    def test_lookup_known_and_unknown_records(self):
        found = enterprise_context.lookup_enterprise_record("VENDOR-4471")
        self.assertTrue(found["found"])
        missing = enterprise_context.lookup_enterprise_record("NOPE")
        self.assertFalse(missing["found"])

    def test_decision_log_is_deterministic(self):
        a = enterprise_context.create_decision_log_entry("s", "approve")
        b = enterprise_context.create_decision_log_entry("s", "approve")
        self.assertEqual(a["entry_id"], b["entry_id"])
        self.assertFalse(a["persisted"])


class QuoteToCashContextToolTests(unittest.TestCase):
    def test_crm_trigger_returns_crm_data(self):
        ready = quote_to_cash_context.crm_get_quote_trigger("OPP-5001")
        self.assertTrue(ready["found"])
        self.assertTrue(ready["quote_ready"])
        self.assertIn("trigger_conditions", ready)
        not_ready = quote_to_cash_context.crm_get_quote_trigger("OPP-5002")
        self.assertFalse(not_ready["quote_ready"])
        self.assertTrue(not_ready["blocking_conditions"])

    def test_customer_profile_returns_customer_data(self):
        profile = quote_to_cash_context.crm_get_customer_profile("ACC-3300")
        self.assertTrue(profile["found"])
        for key in ("customer_name", "address", "msa_status", "account_status", "buying_context"):
            self.assertIn(key, profile)

    def test_catalog_search_returns_sku_data(self):
        result = quote_to_cash_context.product_search_catalog("analytics platform")
        self.assertGreaterEqual(result["match_count"], 1)
        first = result["matches"][0]
        for key in ("sku", "name", "bundle", "list_price"):
            self.assertIn(key, first)

    def test_validate_skus_flags_completeness(self):
        ok = quote_to_cash_context.product_validate_skus(["SKU-ANALYTICS-CORE", "SKU-SUPPORT-PREM"])
        self.assertTrue(ok["all_valid"])
        bad = quote_to_cash_context.product_validate_skus(["SKU-TRAINING-1"])  # unavailable
        self.assertFalse(bad["all_valid"])

    def test_pricing_is_deterministic_and_discounts(self):
        a = quote_to_cash_context.pricing_calculate_quote(["SKU-ANALYTICS-CORE", "SKU-ANALYTICS-EDGE"], 10)
        b = quote_to_cash_context.pricing_calculate_quote(["SKU-ANALYTICS-CORE", "SKU-ANALYTICS-EDGE"], 10)
        self.assertEqual(a, b)
        self.assertEqual(a["subtotal"], 60000)
        self.assertEqual(a["total"], 54000)
        self.assertEqual(a["currency"], "USD")

    def test_legal_terms_return_clauses_and_approvals(self):
        terms = quote_to_cash_context.legal_evaluate_terms("enterprise", 25)
        self.assertIn("clauses", terms)
        self.assertTrue(terms["clauses"])
        self.assertTrue(any("Legal review" in a for a in terms["approvals_required"]))

    def test_quote_package_is_deterministic_and_customer_ready(self):
        a = quote_to_cash_context.quote_format_package("Contoso Manufacturing", 54000, ["SKU-ANALYTICS-CORE"])
        b = quote_to_cash_context.quote_format_package("Contoso Manufacturing", 54000, ["SKU-ANALYTICS-CORE"])
        self.assertEqual(a["quote_id"], b["quote_id"])
        self.assertTrue(a["customer_ready"])
        self.assertIn("Terms & Conditions", a["sections"])


class McpToolBuildTests(unittest.TestCase):
    def test_module_constants(self):
        self.assertEqual(ENTERPRISE_MCP_MODULE, "invocations_scenarios.mcp_servers.enterprise_context")
        self.assertEqual(QUOTE_TO_CASH_MCP_MODULE, "invocations_scenarios.mcp_servers.quote_to_cash_context")
        self.assertEqual(set(MCP_SERVER_MODULES), {"enterprise_context", "quote_to_cash_context"})

    def test_build_tool_selects_server_and_restricts_tools(self):
        spec = AgentSpec(
            "ToolAgent", "x", "y", mcp_tools=("crm_get_quote_trigger",), mcp_server="quote_to_cash_context"
        )
        tool = build_mcp_tool(spec)
        self.assertEqual(tool.approval_mode, "never_require")
        self.assertEqual(list(tool.allowed_tools), ["crm_get_quote_trigger"])

    def test_build_tool_rejects_unknown_server(self):
        spec = AgentSpec("ToolAgent", "x", "y", mcp_tools=("foo",), mcp_server="does_not_exist")
        with self.assertRaises(ValueError):
            build_mcp_tool(spec)


if __name__ == "__main__":
    unittest.main()
