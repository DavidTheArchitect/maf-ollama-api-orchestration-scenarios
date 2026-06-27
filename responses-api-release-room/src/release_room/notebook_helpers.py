from __future__ import annotations

from typing import Any

from .scenarios import ScenarioSpec

PATTERN_ANATOMY: dict[str, dict[str, str]] = {
    "sequential": {
        "control_flow": "Agents run in a fixed order, with each step receiving the prior step's response.",
        "coordination": "The builder defines the chain. The model does not decide which agent acts next.",
        "output_behavior": "Final and intermediate agent responses can be inspected to see the pipeline.",
        "best_when": "Use for repeatable pipelines where every request needs the same stages.",
    },
    "concurrent": {
        "control_flow": "All specialist agents receive the same input and run independently.",
        "coordination": "The builder fans out work and aggregates the participant outputs.",
        "output_behavior": "Each participant contributes a separate perspective.",
        "best_when": "Use when independent reviews can happen in parallel.",
    },
    "handoff": {
        "control_flow": "A start agent routes the conversation to specialists through handoff tools.",
        "coordination": "The model chooses handoffs within the allowed handoff graph.",
        "output_behavior": "Outputs may include function-call records plus specialist messages.",
        "best_when": "Use when the right specialist depends on the user's issue.",
    },
    "group-chat": {
        "control_flow": "Agents take turns in a discussion until the termination condition is met.",
        "coordination": "A selector function chooses the next participant.",
        "output_behavior": "The transcript shows critique, refinement, and convergence.",
        "best_when": "Use when visible debate and iteration improve the answer.",
    },
    "magentic": {
        "control_flow": "A manager agent plans work and delegates dynamically to specialists.",
        "coordination": "The manager replans as the task evolves or stalls.",
        "output_behavior": "Specialist outputs show the manager-led investigation path.",
        "best_when": "Use for open-ended work that needs planning and replanning.",
    },
}


def default_ollama_kwargs() -> dict[str, Any]:
    return {
        "model": "qwen3:14b",
        "temperature": 0,
        "num_ctx": 4096,
        "max_tokens": 500,
        "think": False,
    }


def scenario_summary(scenario: ScenarioSpec) -> dict[str, str]:
    return {
        "id": scenario.id,
        "title": scenario.title,
        "pattern": scenario.pattern,
        "learning_goal": scenario.learning_goal,
        "when_to_use": scenario.when_to_use,
        "sample_input": scenario.sample_input,
    }


def agent_roster(scenario: ScenarioSpec) -> list[dict[str, str]]:
    return [
        {
            "agent": spec.name,
            "description": spec.description,
            "instructions": spec.instructions,
        }
        for spec in scenario.agents
    ]


def pattern_anatomy(scenario: ScenarioSpec) -> dict[str, str]:
    return PATTERN_ANATOMY[scenario.pattern]


def workflow_result_to_text(result: Any) -> str:
    outputs = result.get_outputs() if hasattr(result, "get_outputs") else result
    parts = [agent_response_to_text(output) for output in outputs]
    return "\n\n".join(part for part in parts if part) or "No readable workflow text was produced."


def agent_response_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    text = getattr(value, "text", None)
    if text:
        return str(text)
    messages = getattr(value, "messages", None)
    if messages:
        return "\n".join(part for message in messages if (part := agent_response_to_text(message)))
    contents = getattr(value, "contents", None)
    if contents:
        return "\n".join(part for content in contents if (part := agent_response_to_text(content)))
    result = getattr(value, "result", None)
    if result is not None:
        return agent_response_to_text(result)
    return str(value)


def responses_api_reference(scenario: ScenarioSpec) -> dict[str, Any]:
    return {
        "server_command": (
            f"python -m release_room --scenario {scenario.id} "
            "--model qwen3:14b --max-tokens 500 --port 8088"
        ),
        "endpoint": "http://localhost:8088/responses",
        "payload": {"input": scenario.sample_input, "stream": False},
    }
