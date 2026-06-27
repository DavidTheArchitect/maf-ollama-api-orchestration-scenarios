from __future__ import annotations

from collections.abc import Mapping, Sequence
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
    intermediate_outputs = result.get_intermediate_outputs() if hasattr(result, "get_intermediate_outputs") else []
    if not outputs:
        intermediate_text = join_readable_outputs(intermediate_outputs)
        return intermediate_text or "No workflow output was produced."

    output_text = join_readable_outputs(outputs)
    if intermediate_outputs and should_use_intermediate_outputs(output_text):
        intermediate_text = join_readable_outputs(intermediate_outputs)
        if intermediate_text:
            return intermediate_text

    return output_text or "No readable workflow text was produced."


def join_readable_outputs(outputs: Any) -> str:
    return "\n\n".join(text for output in outputs if (text := agent_response_to_text(output)))


def should_use_intermediate_outputs(output_text: str) -> bool:
    normalized = output_text.strip().lower()
    if not normalized:
        return True
    if len(normalized) >= 160:
        return False
    framework_markers = (
        "termination condition",
        "maximum reset count",
        "maximum stall count",
        "workflow terminated",
    )
    return any(marker in normalized for marker in framework_markers)


def agent_response_to_text(value: Any) -> str:
    text = extract_text(value)
    return text or "No readable workflow text was produced."


def extract_text(value: Any, seen: set[int] | None = None) -> str:
    if value is None:
        return ""
    if seen is None:
        seen = set()
    value_id = id(value)
    if value_id in seen:
        return ""
    seen.add(value_id)

    if isinstance(value, str):
        return "" if is_object_repr(value) else value

    text = getattr(value, "text", None)
    if isinstance(text, str) and text and not is_object_repr(text):
        return text

    messages = getattr(value, "messages", None)
    if messages:
        parts: list[str] = []
        for message in messages:
            author = getattr(message, "author_name", None) or getattr(message, "role", None) or "assistant"
            message_text = extract_text(message, seen)
            if message_text:
                parts.append(f"[{author}] {message_text}")
        if parts:
            return "\n".join(parts)

    contents = getattr(value, "contents", None)
    if contents:
        parts = [extract_text(content, seen) for content in contents]
        return "\n".join(part for part in parts if part)

    items = getattr(value, "items", None)
    if items and not callable(items):
        parts = [extract_text(item, seen) for item in items]
        return "\n".join(part for part in parts if part)

    result = getattr(value, "result", None)
    if result is not None:
        return extract_text(result, seen)

    if isinstance(value, Mapping):
        parts = [extract_text(value.get(key), seen) for key in ("text", "content", "message", "summary", "result")]
        return "\n".join(part for part in parts if part)

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        parts = [extract_text(item, seen) for item in value]
        return "\n".join(part for part in parts if part)

    fallback = str(value)
    return "" if is_object_repr(fallback) else fallback


def is_object_repr(value: str) -> bool:
    return value.startswith("<") and " object at 0x" in value and value.endswith(">")


def responses_api_reference(scenario: ScenarioSpec) -> dict[str, Any]:
    return {
        "server_command": (
            f"python -m release_room --scenario {scenario.id} "
            "--model qwen3:14b --max-tokens 500 --port 8088"
        ),
        "endpoint": "http://localhost:8088/responses",
        "payload": {"input": scenario.sample_input, "stream": False},
    }
