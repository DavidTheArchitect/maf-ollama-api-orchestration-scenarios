"""Offline A2A protocol tests: deterministic partner server + real JSON-RPC.

These tests exercise the genuine A2A wire protocol with zero LLM calls: the
bundled partner server is started in-process on an ephemeral port, and the
framework's ``A2AAgent`` client discovers the agent cards and round-trips
messages over HTTP/JSON-RPC.
"""

import os
import unittest

from review_bot.a2a_servers.partner_agents import (
    PARTNER_AGENTS,
    PARTNER_FIXTURES,
    PartnerA2AServer,
    deterministic_reply,
)
from review_bot.agents import AgentSpec, create_ollama_agent, resolve_a2a_url
from review_bot.scenarios import SCENARIOS_BY_ID

SCENARIO_ID = "group-chat-partner-launch-review"


class PartnerServerRoundTripTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_cards_and_round_trip_over_a2a(self):
        from agent_framework.a2a import A2AAgent

        with PartnerA2AServer() as server:
            for path, spec in PARTNER_AGENTS.items():
                with self.subTest(partner=spec["name"]):
                    agent = A2AAgent(name=spec["name"], url=f"{server.base_url}/{path}")
                    reply = await agent.run("Report your organization's launch-review facts.")
                    text = reply.text or ""
                    self.assertIn(PARTNER_FIXTURES[path]["organization"], text)
                    self.assertEqual(text.strip(), deterministic_reply(path).strip())

    async def test_factory_builds_a2a_agents_for_remote_seats(self):
        from agent_framework.a2a import A2AAgent

        scenario = SCENARIOS_BY_ID[SCENARIO_ID]
        with PartnerA2AServer() as server:
            previous = os.environ.get("A2A_PARTNER_BASE_URL")
            os.environ["A2A_PARTNER_BASE_URL"] = server.base_url
            try:
                remote = [spec for spec in scenario.agents if spec.a2a_url]
                self.assertEqual(len(remote), 2)
                for spec in remote:
                    agent = create_ollama_agent(spec)
                    self.assertIsInstance(agent, A2AAgent)
                    reply = await agent.run("Report your organization's launch-review facts.")
                    self.assertTrue((reply.text or "").strip())
            finally:
                if previous is None:
                    os.environ.pop("A2A_PARTNER_BASE_URL", None)
                else:
                    os.environ["A2A_PARTNER_BASE_URL"] = previous


class PartnerScenarioShapeTests(unittest.TestCase):
    def test_scenario_shape(self):
        scenario = SCENARIOS_BY_ID[SCENARIO_ID]
        self.assertEqual(scenario.pattern, "group-chat")
        self.assertEqual(len(scenario.agents), 5)
        remote = [spec.name for spec in scenario.agents if spec.a2a_url]
        self.assertEqual(remote, ["PartnerSolutionsAgent", "ExternalComplianceAgent"])
        # the chair closes each cycle and declares the termination phrase
        self.assertEqual(scenario.agents[-1].name, "JointLaunchChairAgent")
        self.assertTrue(scenario.termination_phrases)

    def test_remote_seat_names_match_the_partner_server(self):
        scenario = SCENARIOS_BY_ID[SCENARIO_ID]
        served = {spec["name"]: f"/{path}" for path, spec in PARTNER_AGENTS.items()}
        for spec in scenario.agents:
            if not spec.a2a_url:
                continue
            with self.subTest(agent=spec.name):
                self.assertEqual(served.get(spec.name), spec.a2a_url)

    def test_resolve_a2a_url_env_and_absolute(self):
        spec = AgentSpec("X", "d", "i", a2a_url="/partner-solutions")
        previous = os.environ.get("A2A_PARTNER_BASE_URL")
        os.environ["A2A_PARTNER_BASE_URL"] = "http://127.0.0.1:9999/"
        try:
            self.assertEqual(resolve_a2a_url(spec), "http://127.0.0.1:9999/partner-solutions")
        finally:
            if previous is None:
                os.environ.pop("A2A_PARTNER_BASE_URL", None)
            else:
                os.environ["A2A_PARTNER_BASE_URL"] = previous
        absolute = AgentSpec("X", "d", "i", a2a_url="http://example.local/agent")
        self.assertEqual(resolve_a2a_url(absolute), "http://example.local/agent")


if __name__ == "__main__":
    unittest.main()
