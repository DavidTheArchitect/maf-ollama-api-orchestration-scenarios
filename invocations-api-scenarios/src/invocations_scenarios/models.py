from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .scenarios import PATTERN_DEFAULT_SCENARIO, PATTERNS, SCENARIOS_BY_ID, get_scenario, normalize_scenario_id


class RequestValidationError(ValueError):
    pass


@dataclass(frozen=True)
class InvocationRequest:
    scenario: str
    pattern: str
    task: str
    subject: str
    artifacts: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    stream: bool = False


@dataclass(frozen=True)
class InvocationResponse:
    scenario: str
    pattern: str
    agents: list[str]
    summary: str
    recommendations: list[str]
    subject: str
    session_id: str | None = None
    events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "pattern": self.pattern,
            "agents": self.agents,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "subject": self.subject,
            "session_id": self.session_id,
            "events": self.events,
        }


def normalize_pattern(value: Any) -> str:
    normalized = str(value or "concurrent").strip().lower().replace("_", "-")
    if normalized in PATTERNS:
        return normalized
    raise RequestValidationError(f"Unknown pattern '{value}'. Expected one of: {', '.join(PATTERNS)}")


def _string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RequestValidationError(f"'{field_name}' must be a list of strings.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise RequestValidationError(f"'{field_name}' must contain only non-empty strings.")
        result.append(item.strip())
    return result


def _resolve_scenario(payload: dict[str, Any]) -> str:
    scenario_value = payload.get("scenario")
    pattern_value = payload.get("pattern")

    if scenario_value is None and pattern_value is None:
        return PATTERN_DEFAULT_SCENARIO["concurrent"]

    try:
        scenario_id = normalize_scenario_id(scenario_value) if scenario_value is not None else None
    except ValueError as exc:
        raise RequestValidationError(str(exc)) from exc

    if pattern_value is None:
        return scenario_id or PATTERN_DEFAULT_SCENARIO["concurrent"]

    pattern = normalize_pattern(pattern_value)
    if scenario_id is None:
        return PATTERN_DEFAULT_SCENARIO[pattern]

    expected_pattern = SCENARIOS_BY_ID[scenario_id].pattern
    if expected_pattern != pattern:
        raise RequestValidationError(
            f"Scenario '{scenario_id}' uses pattern '{expected_pattern}', but request supplied pattern '{pattern}'."
        )
    return scenario_id


def parse_invocation_request(payload: Any) -> InvocationRequest:
    if not isinstance(payload, dict):
        raise RequestValidationError("Request body must be a JSON object.")

    task = payload.get("task")
    if not isinstance(task, str) or not task.strip():
        raise RequestValidationError("'task' is required and must be a non-empty string.")

    # 'repo' is an accepted alias for 'subject' (documented in the OpenAPI
    # spec); the default applies only when neither key is present.
    subject = payload.get("subject", payload.get("repo", "unspecified subject"))
    if not isinstance(subject, str) or not subject.strip():
        raise RequestValidationError("'subject' must be a non-empty string when supplied.")

    stream = payload.get("stream", False)
    if not isinstance(stream, bool):
        raise RequestValidationError("'stream' must be a boolean when supplied.")

    scenario_id = _resolve_scenario(payload)
    scenario = get_scenario(scenario_id)
    # 'changed_files' is an accepted alias for 'artifacts' (documented in the
    # OpenAPI spec).
    artifacts = payload.get("artifacts", payload.get("changed_files"))

    return InvocationRequest(
        scenario=scenario.id,
        pattern=scenario.pattern,
        task=task.strip(),
        subject=subject.strip(),
        artifacts=_string_list(artifacts, "artifacts"),
        constraints=_string_list(payload.get("constraints"), "constraints"),
        stream=stream,
    )


def build_invocation_prompt(request: InvocationRequest, previous_turns: list[str] | None = None) -> str:
    scenario = get_scenario(request.scenario)
    artifacts = "\n".join(f"- {item}" for item in request.artifacts) or "- No artifacts supplied."
    constraints = "\n".join(f"- {item}" for item in request.constraints) or "- No explicit constraints."
    history = "\n".join(previous_turns or []) or "No prior turns for this session."
    return (
        f"Scenario: {scenario.id} - {scenario.title}\n"
        f"Pattern: {scenario.pattern}\n"
        f"Learning goal: {scenario.learning_goal}\n"
        f"Subject: {request.subject}\n"
        f"Task: {request.task}\n\n"
        f"Artifacts:\n{artifacts}\n\n"
        f"Constraints:\n{constraints}\n\n"
        f"Session context:\n{history}\n\n"
        "Return actionable findings. Do not claim to have inspected artifacts beyond the provided names and context."
    )
