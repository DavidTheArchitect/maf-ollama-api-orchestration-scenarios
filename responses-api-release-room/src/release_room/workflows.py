from __future__ import annotations

from typing import Any

from .agents import OllamaAgentConfig, build_ollama_config, create_ollama_agent
from .scenarios import SCENARIO_IDS, ScenarioSpec, get_scenario, normalize_scenario_id

WORKFLOW_NAMES: tuple[str, ...] = SCENARIO_IDS


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
    if scenario.pattern == "sequential":
        return build_sequential_workflow(scenario, config=config)
    if scenario.pattern == "concurrent":
        return build_concurrent_workflow(scenario, config=config)
    if scenario.pattern == "handoff":
        return build_handoff_workflow(scenario, config=config)
    if scenario.pattern == "group-chat":
        return build_group_chat_workflow(scenario, config=config)
    if scenario.pattern == "magentic":
        return build_magentic_workflow(scenario, config=config)
    raise ValueError(f"Unsupported pattern '{scenario.pattern}' for scenario '{scenario.id}'.")


def _agents_for(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> list[Any]:
    return [create_ollama_agent(spec, config=config) for spec in scenario.agents]


def build_sequential_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    from agent_framework.orchestrations import SequentialBuilder

    participants = _agents_for(scenario, config=config or build_ollama_config())
    return SequentialBuilder(
        participants=participants,
        chain_only_agent_responses=True,
        intermediate_output_from=participants[:-1],
    ).build()


def build_concurrent_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    from agent_framework.orchestrations import ConcurrentBuilder

    participants = _agents_for(scenario, config=config or build_ollama_config())
    return ConcurrentBuilder(participants=participants).build()


def build_handoff_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    from agent_framework.orchestrations import HandoffBuilder

    participants = _agents_for(scenario, config=config or build_ollama_config())
    triage = participants[0]
    specialists = participants[1:]

    def stop_after_specialist(messages: list[Any]) -> bool:
        assistant_messages = [m for m in messages if getattr(m, "role", None) == "assistant"]
        return len(assistant_messages) >= 3

    builder = HandoffBuilder(
        name=scenario.id,
        participants=participants,
        termination_condition=stop_after_specialist,
    ).with_start_agent(triage)

    builder = builder.add_handoff(triage, specialists)
    for specialist in specialists:
        builder = builder.add_handoff(specialist, [triage])

    return builder.build()


def build_group_chat_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig | None = None) -> Any:
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
