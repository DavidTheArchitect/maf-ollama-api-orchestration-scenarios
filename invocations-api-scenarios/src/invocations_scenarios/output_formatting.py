from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

#: Below this length, a final output that also matches a framework marker is
#: treated as a status stub and the intermediate outputs are shown instead.
_MIN_READABLE_OUTPUT_CHARS = 160


def workflow_result_to_text(events: Any) -> str:
    outputs = events.get_outputs() if hasattr(events, "get_outputs") else events
    intermediate_outputs = events.get_intermediate_outputs() if hasattr(events, "get_intermediate_outputs") else []
    if not outputs:
        intermediate_text = join_readable_outputs(intermediate_outputs)
        return clean_workflow_text(intermediate_text) or "No workflow output was produced."

    output_text = join_readable_outputs(outputs)
    if intermediate_outputs and should_use_intermediate_outputs(output_text):
        intermediate_text = join_readable_outputs(intermediate_outputs)
        if intermediate_text:
            return clean_workflow_text(intermediate_text)

    return clean_workflow_text(output_text) or "No readable workflow text was produced."


def join_readable_outputs(outputs: Any) -> str:
    return "\n\n".join(text for output in outputs if (text := agent_response_to_text(output)))


def should_use_intermediate_outputs(output_text: str) -> bool:
    normalized = output_text.strip().lower()
    if not normalized:
        return True
    if len(normalized) >= _MIN_READABLE_OUTPUT_CHARS:
        return False
    framework_markers = (
        "termination condition",
        "maximum reset count",
        "maximum stall count",
        "workflow terminated",
        "group chat has reached its termination condition",
    )
    return any(marker in normalized for marker in framework_markers)


def agent_response_to_text(value: Any) -> str:
    return clean_workflow_text(extract_text(value))


def clean_workflow_text(text: str) -> str:
    """Remove leading framework status lines when useful scenario text follows."""

    lines = text.splitlines()
    while lines and is_framework_status_line(lines[0]) and any(line.strip() for line in lines[1:]):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def is_framework_status_line(line: str) -> bool:
    normalized = line.strip().lower()
    return (
        normalized.startswith("invalid next speaker:")
        or normalized.startswith("magentic orchestrator:")
        or normalized.startswith("maximum consecutive function call errors reached")
    )


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
    """Heuristic for default ``object.__repr__`` text (``<X object at 0x...>``).

    Only catches the default repr shape; custom ``__repr__`` output passes
    through, and legitimate text that happens to match is discarded. Both are
    acceptable for readable-output filtering in a learning sample.
    """

    return value.startswith("<") and " object at 0x" in value and value.endswith(">")
