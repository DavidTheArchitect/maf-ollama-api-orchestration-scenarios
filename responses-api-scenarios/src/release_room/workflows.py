"""Workflow construction for the Responses API sample.

Sequential, Concurrent, and Handoff are built as explicit
:class:`~agent_framework.WorkflowBuilder` graphs of code-defined executors
(see :mod:`release_room.executors`) with agent nodes wrapped in
:class:`~agent_framework.AgentExecutor`. Group Chat and Magentic use the
framework's code-driven orchestration builders (custom selection function,
manager planning, and ledger logic). Agent nodes are LLM-backed specialists
with role instructions; MCP tools are attached only where the scenario teaches
tool-grounded context.
"""

from __future__ import annotations

import re
from typing import Any

from .agents import OllamaAgentConfig, build_ollama_config, create_ollama_agent
from .executors import (
    ConcurrentAggregatorExecutor,
    ConcurrentSynthesisGateExecutor,
    HandoffFinisherGateExecutor,
    HandoffOutputExecutor,
    HandoffRouterExecutor,
    PromptDispatchExecutor,
    SequentialOutputExecutor,
    StageGateExecutor,
)
from .scenarios import SCENARIO_IDS, ScenarioSpec, get_scenario, normalize_scenario_id

WORKFLOW_NAMES: tuple[str, ...] = SCENARIO_IDS

_STOPWORDS = {"agent", "specialist", "the", "and", "for", "with", "that", "from", "into"}


def normalize_workflow_name(value: str | None) -> str:
    """Backward-compatible alias for the old workflow selector."""

    return normalize_scenario_id(value)


def build_release_workflow(
    scenario_id: str | None = None,
    *,
    model: str | None = None,
    ollama_host: str | None = None,
    temperature: float | None = None,
    num_ctx: int | None = None,
    max_tokens: int | None = None,
    keep_alive: str | None = None,
    think: bool | None = None,
) -> Any:
    scenario = get_scenario(scenario_id)
    config = build_ollama_config(
        model=model,
        host=ollama_host,
        temperature=temperature,
        num_ctx=num_ctx,
        max_tokens=max_tokens,
        keep_alive=keep_alive,
        think=think,
    )
    builders = {
        "sequential": build_sequential_workflow,
        "concurrent": build_concurrent_workflow,
        "handoff": build_handoff_workflow,
        "group-chat": build_group_chat_workflow,
        "magentic": build_magentic_workflow,
    }
    try:
        builder = builders[scenario.pattern]
    except KeyError as exc:
        raise ValueError(f"Unsupported pattern '{scenario.pattern}' for scenario '{scenario.id}'.") from exc
    return builder(scenario, config=config)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _agents_for(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> list[Any]:
    return [create_ollama_agent(spec, config=config) for spec in scenario.agents]


def _agent_executor(spec_index: int, scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
    from agent_framework import AgentExecutor

    spec = scenario.agents[spec_index]
    agent = create_ollama_agent(spec, config=config)
    return AgentExecutor(agent, id=_slug(spec.name))


def _route_keywords(spec: Any) -> tuple[str, ...]:
    if getattr(spec, "route_keywords", ()):
        return tuple(spec.route_keywords)
    tokens = re.findall(r"[a-z]+", f"{spec.name} {spec.description}".lower())
    keywords = [token for token in tokens if len(token) > 3 and token not in _STOPWORDS]
    return tuple(dict.fromkeys(keywords))[:6]


def default_sample_max_tokens(scenario: ScenarioSpec) -> int:
    """Token budget for a sample run: 500 for Magentic, 250 for the rest."""

    return 500 if scenario.pattern == "magentic" else 250


async def run_scenario_sample(
    scenario_id: str | None = None,
    *,
    max_tokens: int | None = None,
    **config_overrides: Any,
) -> str:
    """Build and run a scenario in-process and return readable output text."""

    from .notebook_helpers import workflow_result_to_text

    scenario = get_scenario(scenario_id)
    tokens = max_tokens if max_tokens is not None else default_sample_max_tokens(scenario)
    workflow = build_release_workflow(scenario.id, max_tokens=tokens, **config_overrides)
    result = await workflow.run(scenario.sample_input)
    return workflow_result_to_text(result)


def build_sequential_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    """Sequential graph: dispatch -> agent -> gate -> ... -> agent -> output."""

    from agent_framework import WorkflowBuilder

    config = config or build_ollama_config()
    agents = [_agent_executor(i, scenario, config=config) for i in range(len(scenario.agents))]
    dispatch = PromptDispatchExecutor(id="dispatch")
    last_name = scenario.agents[-1].name
    output = SequentialOutputExecutor(id="final_output", stage_name=last_name)

    builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
    builder.add_edge(dispatch, agents[0])
    for index in range(len(agents) - 1):
        gate = StageGateExecutor(id=f"gate_{index}", stage_name=scenario.agents[index].name)
        builder.add_edge(agents[index], gate)
        builder.add_edge(gate, agents[index + 1])
    builder.add_edge(agents[-1], output)
    return builder.build()


def build_concurrent_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    """Concurrent graph: dispatch fans out, then fan-in ends or feeds a synthesizer.

    Without ``concurrent_synthesizer``, all agents run in parallel and a code
    aggregator labels and joins their outputs. With it, the named agent is held
    out of the fan-out and instead runs after fan-in, receiving every labelled
    parallel finding so it can genuinely combine them.
    """

    from agent_framework import WorkflowBuilder

    config = config or build_ollama_config()
    synthesizer_name = scenario.concurrent_synthesizer
    parallel = [i for i in range(len(scenario.agents)) if scenario.agents[i].name != synthesizer_name]
    if synthesizer_name is not None and len(parallel) == len(scenario.agents):
        raise ValueError(
            f"concurrent_synthesizer '{synthesizer_name}' is not an agent of scenario '{scenario.id}'."
        )
    agents = [_agent_executor(i, scenario, config=config) for i in parallel]
    parallel_names = [scenario.agents[i].name for i in parallel]
    dispatch = PromptDispatchExecutor(id="dispatch")

    if synthesizer_name is None:
        aggregator = ConcurrentAggregatorExecutor(id="aggregator", agent_names=parallel_names)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[aggregator])
        builder.add_fan_out_edges(dispatch, agents)
        builder.add_fan_in_edges(agents, aggregator)
        return builder.build()

    synthesizer_index = next(
        i for i in range(len(scenario.agents)) if scenario.agents[i].name == synthesizer_name
    )
    synthesizer = _agent_executor(synthesizer_index, scenario, config=config)
    gate = ConcurrentSynthesisGateExecutor(id="synthesis_gate", agent_names=parallel_names)
    output = SequentialOutputExecutor(id="final_output", stage_name=synthesizer_name)
    builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
    builder.add_fan_out_edges(dispatch, agents)
    builder.add_fan_in_edges(agents, gate)
    builder.add_edge(gate, synthesizer)
    builder.add_edge(synthesizer, output)
    return builder.build()


def build_handoff_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    """Handoff graph: dispatch -> triage -> router -> one specialist -> output.

    The triage agent names the route (``ROUTE: <SpecialistName>``); the router
    validates it against the allowed routes, falling back to keyword scoring.
    When the scenario declares ``handoff_finisher``, the routed specialist's
    output flows through a gate to that fixed finishing agent, so every run
    ends with the designated owner producing the final deliverable.
    """

    from agent_framework import WorkflowBuilder

    config = config or build_ollama_config()
    triage = _agent_executor(0, scenario, config=config)
    finisher_name = scenario.handoff_finisher
    routable = [
        i for i in range(1, len(scenario.agents)) if scenario.agents[i].name != finisher_name
    ]
    if finisher_name is not None and len(routable) == len(scenario.agents) - 1:
        raise ValueError(
            f"handoff_finisher '{finisher_name}' is not an agent of scenario '{scenario.id}'."
        )
    specialists = [_agent_executor(i, scenario, config=config) for i in routable]
    specialist_ids = [_slug(scenario.agents[i].name) for i in routable]
    routes = {specialist_ids[pos]: _route_keywords(scenario.agents[i]) for pos, i in enumerate(routable)}
    display_names = {specialist_ids[pos]: scenario.agents[i].name for pos, i in enumerate(routable)}
    dispatch = PromptDispatchExecutor(id="dispatch")
    router = HandoffRouterExecutor(
        id="router", routes=routes, default_route=specialist_ids[0], display_names=display_names
    )
    output = HandoffOutputExecutor(id="final_output", stage_name=finisher_name)

    builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
    builder.add_edge(dispatch, triage)
    builder.add_edge(triage, router)
    if finisher_name is None:
        for specialist in specialists:
            builder.add_edge(router, specialist)
            builder.add_edge(specialist, output)
        return builder.build()

    finisher_index = next(i for i in range(1, len(scenario.agents)) if scenario.agents[i].name == finisher_name)
    finisher = _agent_executor(finisher_index, scenario, config=config)
    finisher_gate = HandoffFinisherGateExecutor(id="finisher_gate")
    for specialist in specialists:
        builder.add_edge(router, specialist)
        builder.add_edge(specialist, finisher_gate)
    builder.add_edge(finisher_gate, finisher)
    builder.add_edge(finisher, output)
    return builder.build()


def build_group_chat_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    """Group Chat: code-defined round-robin selection and termination."""

    from agent_framework.orchestrations import GroupChatBuilder, GroupChatState

    participants = _agents_for(scenario, config=config or build_ollama_config())

    def round_robin_selector(state: GroupChatState) -> str:
        participant_names = list(state.participants.keys())
        return participant_names[state.current_round % len(participant_names)]

    def stop_after_council(messages: list[Any]) -> bool:
        assistant_messages = [m for m in messages if getattr(m, "role", None) == "assistant"]
        if len(assistant_messages) >= 7:
            return True
        last_text = getattr(messages[-1], "text", "").lower() if messages else ""
        return "approved" in last_text and "recommendation" in last_text

    return GroupChatBuilder(
        participants=participants,
        selection_func=round_robin_selector,
        termination_condition=stop_after_council,
        intermediate_output_from=participants,
    ).build()


def build_magentic_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    """Magentic: code-defined manager plans and delegates to specialists."""

    from agent_framework.orchestrations import MagenticBuilder

    agents = _agents_for(scenario, config=config or build_ollama_config())
    manager_agent = agents[0]
    participants = agents[1:]
    return MagenticBuilder(
        participants=participants,
        intermediate_output_from=participants,
        manager_agent=manager_agent,
        max_round_count=10,
        max_stall_count=3,
        max_reset_count=2,
    ).build()
