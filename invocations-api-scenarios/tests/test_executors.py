import unittest

from agent_framework import AgentResponse, BaseAgent, Message

import review_bot.workflows as workflows
from review_bot.output_formatting import workflow_result_to_text
from review_bot.scenarios import get_scenario

_STOP_MARKERS = (
    "termination condition",
    "maximum reset count",
    "maximum stall count",
    "workflow terminated",
)


class _StubAgent(BaseAgent):
    """Deterministic agent used to exercise the graph wiring without Ollama."""

    async def run(self, messages=None, *, session=None, **kwargs):
        return AgentResponse(
            messages=[Message(role="assistant", contents=[f"[{self.name}] produced a concrete result"])]
        )

    async def run_stream(self, messages=None, *, session=None, **kwargs):
        yield await self.run(messages, session=session, **kwargs)


class GraphExecutorTests(unittest.IsolatedAsyncioTestCase):
    """The custom-executor graphs (sequential/concurrent/handoff) run offline."""

    def setUp(self):
        self._original = workflows.create_ollama_agent
        workflows.create_ollama_agent = lambda spec, *, config=None: _StubAgent(name=spec.name)

    def tearDown(self):
        workflows.create_ollama_agent = self._original

    async def _run(self, scenario_id: str) -> str:
        scenario = get_scenario(scenario_id)
        workflow = workflows.build_review_workflow(scenario_id)
        result = await workflow.run(scenario.sample_task)
        return workflow_result_to_text(result)

    async def test_sequential_graph_runs(self):
        text = await self._run("sequential-release-readiness")
        self.assertTrue(text.strip())
        for spec in get_scenario("sequential-release-readiness").agents:
            self.assertIn(spec.name, text)

    async def test_concurrent_graph_aggregates(self):
        scenario = get_scenario("concurrent-pr-review")
        text = await self._run(scenario.id)
        self.assertTrue(text.strip())
        for spec in scenario.agents:
            self.assertIn(spec.name, text)

    async def test_handoff_graph_routes_to_specialist(self):
        text = await self._run("handoff-support-triage")
        self.assertTrue(text.strip())
        self.assertIn("routed to", text)

    async def test_handoff_finisher_always_completes_the_run(self):
        for scenario_id, finisher in (
            ("handoff-claims-exception-routing", "CustomerCommsAgent"),
            ("scenario-16-quote-to-cash-handoff", "QuoteGenerationAgent"),
        ):
            with self.subTest(scenario=scenario_id):
                scenario = get_scenario(scenario_id)
                self.assertEqual(scenario.handoff_finisher, finisher)
                text = await self._run(scenario_id)
                self.assertIn("routed to", text)
                self.assertIn(finisher, text)

    async def test_output_is_not_only_a_stop_marker(self):
        for scenario_id in (
            "sequential-procurement-approval",
            "concurrent-security-alert-enrichment",
            "scenario-16-quote-to-cash-handoff",
        ):
            with self.subTest(scenario=scenario_id):
                text = await self._run(scenario_id)
                normalized = text.strip().lower()
                self.assertTrue(normalized)
                self.assertFalse(any(marker in normalized for marker in _STOP_MARKERS))


class HandoffRouterDirectiveTests(unittest.TestCase):
    """The router honors valid ROUTE directives and falls back to keywords."""

    def _router(self):
        from review_bot.executors import HandoffRouterExecutor

        return HandoffRouterExecutor(
            id="router",
            routes={
                "fraud_specialist_agent": ("fraud", "signal"),
                "payment_specialist_agent": ("payment", "release"),
            },
            default_route="payment_specialist_agent",
        )

    def test_route_directive_wins_over_keywords(self):
        router = self._router()
        text = "The payment threshold is exceeded but there is a fraud signal.\nROUTE: FraudSpecialistAgent"
        self.assertEqual(router.choose(text), "fraud_specialist_agent")

    def test_invalid_directive_falls_back_to_keyword_scoring(self):
        router = self._router()
        text = "Release the payment for this claim.\nROUTE: NoSuchAgent"
        self.assertEqual(router.choose(text), "payment_specialist_agent")

    def test_last_directive_is_honored(self):
        router = self._router()
        text = "ROUTE: PaymentSpecialistAgent\nOn reflection the fraud signal matters more.\nROUTE: FraudSpecialistAgent"
        self.assertEqual(router.choose(text), "fraud_specialist_agent")


if __name__ == "__main__":
    unittest.main()
