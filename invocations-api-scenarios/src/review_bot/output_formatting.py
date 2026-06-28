from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def workflow_result_to_text(events: Any) -> str:
    outputs = events.get_outputs() if hasattr(events, "get_outputs") else events
    intermediate_outputs = events.get_intermediate_outputs() if hasattr(events, "get_intermediate_outputs") else []
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


def agent_response_to_text(response: Any) -> str:
    text = extract_text(response)
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
