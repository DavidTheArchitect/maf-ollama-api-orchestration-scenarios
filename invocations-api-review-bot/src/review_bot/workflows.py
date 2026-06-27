from __future__ import annotations

from typing import Any

from .agents import OllamaAgentConfig, build_ollama_config, create_ollama_agent
from .models import ReviewRequest, ReviewResponse, build_review_prompt
from .output_formatting import workflow_result_to_text
from .scenarios import ScenarioSpec, get_scenario


def _agents_for(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> list[Any]:
    return [create_ollama_agent(spec, config=config) for spec in scenario.agents]


def build_review_workflow(
    scenario: ScenarioSpec | str | None = None,
    *,
    model: str | None = None,
    ollama_host: str | None = None,
    temperature: float | None = None,
    num_ctx: int | None = None,
    max_tokens: int | None = None,
    keep_alive: str | None = None,
    think: bool | None = None,
) -> Any:
    scenario = scenario if isinstance(scenario, ScenarioSpec) else get_scenario(scenario)
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

    def stop_after_advisory(messages: list[Any]) -> bool:
        assistant_messages = [m for m in messages if getattr(m, "role", None) == "assistant"]
        if len(assistant_messages) >= 7:
            return True
        last_text = getattr(messages[-1], "text", "").lower() if messages else ""
        return "approved" in last_text and "recommendation" in last_text

    return GroupChatBuilder(
        participants=participants,
        selection_func=round_robin_selector,
        termination_condition=stop_after_advisory,
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


async def run_review(
    request: ReviewRequest,
    *,
    session_id: str | None = None,
    previous_turns: list[str] | None = None,
    model: str | None = None,
    ollama_host: str | None = None,
    temperature: float | None = None,
    num_ctx: int | None = None,
    max_tokens: int | None = None,
    keep_alive: str | None = None,
    think: bool | None = None,
) -> ReviewResponse:
    scenario = get_scenario(request.scenario)
    prompt = build_review_prompt(request, previous_turns)
    workflow = build_review_workflow(
        scenario,
        model=model,
        ollama_host=ollama_host,
        temperature=temperature,
        num_ctx=num_ctx,
        max_tokens=max_tokens,
        keep_alive=keep_alive,
        think=think,
    )
    output_text = await _run_workflow_for_text(workflow, prompt)

    return ReviewResponse(
        scenario=scenario.id,
        pattern=scenario.pattern,
        agents=[agent.name for agent in scenario.agents],
        summary=output_text,
        recommendations=_recommendations_from_text(output_text),
        subject=request.subject,
        session_id=session_id,
        events=[f"ran:{scenario.pattern}", f"agents:{len(scenario.agents)}"],
    )


async def _run_workflow_for_text(workflow: Any, prompt: str) -> str:
    events = await workflow.run(prompt)
    return workflow_result_to_text(events)


def _recommendations_from_text(text: str) -> list[str]:
    lines = [line.strip(" -\t") for line in text.splitlines()]
    recommendations = [line for line in lines if line and len(line) < 180][:5]
    return recommendations or ["Review the summary and decide whether follow-up specialist review is needed."]
