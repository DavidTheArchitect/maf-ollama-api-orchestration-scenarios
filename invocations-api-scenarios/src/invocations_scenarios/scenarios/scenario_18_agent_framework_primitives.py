"""Agent Framework primitives lab scenario for the Invocations API sample.

Run directly:
    python -m invocations_scenarios.scenarios.scenario_18_agent_framework_primitives
"""

from __future__ import annotations

from ..agents import AgentSpec
from ._runner import main, run_sample
from .types import ScenarioSpec


SCENARIO = ScenarioSpec(
    id="scenario-18-agent-framework-primitives",
    pattern="sequential",
    title="Agent Framework Primitives Lab",
    learning_goal=(
        "Learn the practical Microsoft Agent Framework building blocks in one scenario: messages, "
        "agents, tools, MCP, A2A, workflows, executors, orchestration builders, hosting, and observability."
    ),
    when_to_use=(
        "Use this lab when learners need a map of the framework primitives before choosing a specific "
        "orchestration pattern or production hosting boundary."
    ),
    sample_task=(
        "Create an engineering enablement brief for a new Agent Framework team. The brief must explain "
        "which primitives to use for a local Ollama prototype, how tool grounding and remote agents fit, "
        "how workflow routing stays observable, and which primitives are intentionally out of scope for "
        "this local sample."
    ),
    agents=(
        AgentSpec(
            "PrimitiveMapAgent",
            "Maps the framework building blocks.",
            "Summarize the Agent Framework primitives in a clear learning order. Name what each primitive owns.",
        ),
        AgentSpec(
            "AgentRuntimeAgent",
            "Explains agents, messages, tools, sessions, and streaming.",
            "Explain how ChatClient-backed agents consume messages, call tools, maintain session context, and stream output.",
        ),
        AgentSpec(
            "WorkflowGraphAgent",
            "Explains explicit workflow graphs.",
            "Explain WorkflowBuilder, Executor, handler, WorkflowContext state, AgentExecutor nodes, routing, fan-out, and fan-in.",
        ),
        AgentSpec(
            "ProtocolIntegrationAgent",
            "Explains MCP, A2A, and hosting boundaries.",
            "Explain when to use local MCP tools, remote A2A agents, Responses hosting, and Invocations hosting.",
        ),
        AgentSpec(
            "ObservabilityCoachAgent",
            "Turns the primitive map into a teaching checklist.",
            "Synthesize the prior stages into a concise checklist with observability probes and primitives excluded from this local lab.",
        ),
    ),
)


if __name__ == "__main__":
    main(SCENARIO)
