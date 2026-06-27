from __future__ import annotations

from .concurrent_pr_review import SCENARIO as CONCURRENT_PR_REVIEW
from .group_chat_launch_council import SCENARIO as GROUP_CHAT_LAUNCH_COUNCIL
from .handoff_support_triage import SCENARIO as HANDOFF_SUPPORT_TRIAGE
from .magentic_incident_response import SCENARIO as MAGENTIC_INCIDENT_RESPONSE
from .sequential_release_readiness import SCENARIO as SEQUENTIAL_RELEASE_READINESS
from .types import ScenarioSpec

SCENARIOS: tuple[ScenarioSpec, ...] = (
    SEQUENTIAL_RELEASE_READINESS,
    CONCURRENT_PR_REVIEW,
    HANDOFF_SUPPORT_TRIAGE,
    GROUP_CHAT_LAUNCH_COUNCIL,
    MAGENTIC_INCIDENT_RESPONSE,
)

SCENARIOS_BY_ID: dict[str, ScenarioSpec] = {scenario.id: scenario for scenario in SCENARIOS}
SCENARIO_IDS: tuple[str, ...] = tuple(scenario.id for scenario in SCENARIOS)
PATTERNS: tuple[str, ...] = tuple(dict.fromkeys(scenario.pattern for scenario in SCENARIOS))
PATTERN_DEFAULT_SCENARIO: dict[str, str] = {scenario.pattern: scenario.id for scenario in SCENARIOS}
SCENARIO_ALIASES: dict[str, str] = {
    "sequential": "sequential-release-readiness",
    "concurrent": "concurrent-pr-review",
    "handoff": "handoff-support-triage",
    "group": "group-chat-launch-council",
    "groupchat": "group-chat-launch-council",
    "group-chat": "group-chat-launch-council",
    "magentic": "magentic-incident-response",
}


def normalize_scenario_id(value: str | None) -> str:
    normalized = (value or "concurrent-pr-review").strip().lower().replace("_", "-")
    normalized = SCENARIO_ALIASES.get(normalized, normalized)
    if normalized not in SCENARIOS_BY_ID:
        raise ValueError(f"Unknown scenario '{value}'. Expected one of: {', '.join(SCENARIO_IDS)}")
    return normalized


def get_scenario(value: str | None) -> ScenarioSpec:
    return SCENARIOS_BY_ID[normalize_scenario_id(value)]


__all__ = [
    "CONCURRENT_PR_REVIEW",
    "GROUP_CHAT_LAUNCH_COUNCIL",
    "HANDOFF_SUPPORT_TRIAGE",
    "MAGENTIC_INCIDENT_RESPONSE",
    "PATTERN_DEFAULT_SCENARIO",
    "PATTERNS",
    "SCENARIO_ALIASES",
    "SCENARIO_IDS",
    "SCENARIOS",
    "SCENARIOS_BY_ID",
    "SEQUENTIAL_RELEASE_READINESS",
    "ScenarioSpec",
    "get_scenario",
    "normalize_scenario_id",
]
