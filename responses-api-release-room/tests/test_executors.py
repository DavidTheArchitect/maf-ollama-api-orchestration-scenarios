import unittest

from agent_framework import AgentResponse, BaseAgent, Message

import release_room.workflows as workflows
from release_room.notebook_helpers import workflow_result_to_text
from release_room.scenarios import get_scenario

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
        workflow = workflows.build_release_workflow(scenario_id)
        result = await workflow.run(scenario.sample_input)
        return workflow_result_to_text(result)

    async def test_sequential_graph_runs(self):
        text = await self._run("sequential-release-readiness")
        self.assertTrue(text.strip())
        # every stage should appear in the accumulated transcript
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


if __name__ == "__main__":
    unittest.main()
