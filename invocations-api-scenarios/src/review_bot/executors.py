"""Code-defined workflow executors for the orchestration graphs.

These custom :class:`~agent_framework.Executor` subclasses are the code-defined glue of
the advanced workflows. They use typed ``@handler`` methods, read and write
shared :class:`~agent_framework.WorkflowContext` state, route conditionally, and
fan results in — none of this logic lives in a prompt. Agent nodes are wrapped
with :class:`~agent_framework.AgentExecutor` so an instruction-led LLM agent,
with optional MCP tools, runs at each step.

The same executors are exercised offline in tests with a deterministic stub
agent and live with Ollama agents, so the graph wiring is verified without a
model.
"""

from __future__ import annotations

from typing import Any

from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    WorkflowContext,
    handler,
)
from typing_extensions import Never

_TRANSCRIPT_KEY = "transcript"


def make_request(text: str) -> AgentExecutorRequest:
    """Wrap text as a single-user-message agent request."""

    return AgentExecutorRequest(messages=[Message(role="user", contents=[text])])


def response_text(response: AgentExecutorResponse) -> str:
    """Best-effort readable text from an agent executor response."""

    agent_response = getattr(response, "agent_response", None)
    return (getattr(agent_response, "text", None) or "").strip()


def _append_transcript(ctx: WorkflowContext[Any], author: str, text: str) -> list[str]:
    transcript = list(ctx.get_state(_TRANSCRIPT_KEY) or [])
    transcript.append(f"[{author}] {text}")
    ctx.set_state(_TRANSCRIPT_KEY, transcript)
    return transcript


class PromptDispatchExecutor(Executor):
    """Entry executor: normalize the incoming prompt and seed shared state."""

    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        ctx.set_state("prompt", prompt)
        ctx.set_state(_TRANSCRIPT_KEY, [])
        await ctx.send_message(make_request(prompt))


class StageGateExecutor(Executor):
    """Sequential gate between stages: accumulate context and forward it.

    Records the prior stage's output in the shared transcript and forwards the
    full running context to the next stage, so each agent sees everything so far.
    """

    def __init__(self, id: str, *, stage_name: str) -> None:
        super().__init__(id=id)
        self._stage_name = stage_name

    @handler
    async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        transcript = _append_transcript(ctx, self._stage_name, response_text(response))
        prompt = ctx.get_state("prompt") or ""
        carried = "\n".join(transcript)
        await ctx.send_message(make_request(f"Original request:\n{prompt}\n\nWork so far:\n{carried}"))


class SequentialOutputExecutor(Executor):
    """Terminal executor for the sequential graph: emit the full transcript."""

    def __init__(self, id: str, *, stage_name: str) -> None:
        super().__init__(id=id)
        self._stage_name = stage_name

    @handler
    async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
        transcript = _append_transcript(ctx, self._stage_name, response_text(response))
        await ctx.yield_output("\n\n".join(transcript))


class ConcurrentAggregatorExecutor(Executor):
    """Fan-in executor: merge independent specialist responses into one output."""

    def __init__(self, id: str, *, agent_names: list[str]) -> None:
        super().__init__(id=id)
        self._agent_names = agent_names

    @handler
    async def aggregate(
        self, responses: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]
    ) -> None:
        labelled: list[str] = []
        for index, response in enumerate(responses):
            name = self._agent_names[index] if index < len(self._agent_names) else f"agent{index + 1}"
            labelled.append(f"[{name}]\n{response_text(response)}")
        await ctx.yield_output("\n\n".join(labelled))


class HandoffRouterExecutor(Executor):
    """Route the triage result to exactly one specialist by code decision.

    The routing keywords are supplied per scenario. The decision is computed in
    code from the triage agent's text, recorded in shared state, and the request
    is sent to the chosen specialist executor by ``target_id``.
    """

    def __init__(self, id: str, *, routes: dict[str, tuple[str, ...]], default_route: str) -> None:
        super().__init__(id=id)
        self._routes = routes
        self._default_route = default_route

    def choose(self, text: str) -> str:
        lowered = text.lower()
        best_route, best_hits = self._default_route, 0
        for route, keywords in self._routes.items():
            hits = sum(1 for keyword in keywords if keyword in lowered)
            if hits > best_hits:
                best_route, best_hits = route, hits
        return best_route

    @handler
    async def route(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        triage_text = response_text(response)
        chosen = self.choose(triage_text)
        ctx.set_state("route", chosen)
        prompt = ctx.get_state("prompt") or ""
        await ctx.send_message(
            make_request(f"Triage routed this to you.\nRequest:\n{prompt}\n\nTriage notes:\n{triage_text}"),
            target_id=chosen,
        )


class HandoffOutputExecutor(Executor):
    """Terminal executor for the handoff graph: emit the specialist result."""

    @handler
    async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
        route = ctx.get_state("route") or "specialist"
        await ctx.yield_output(f"[routed to {route}]\n{response_text(response)}")
