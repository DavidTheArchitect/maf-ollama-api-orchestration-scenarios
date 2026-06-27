from __future__ import annotations

from .concurrent_pr_review import SCENARIO as CONCURRENT_PR_REVIEW
from .concurrent_security_alert_enrichment import SCENARIO as CONCURRENT_SECURITY_ALERT_ENRICHMENT
from .concurrent_vendor_risk_assessment import SCENARIO as CONCURRENT_VENDOR_RISK_ASSESSMENT
from .group_chat_launch_council import SCENARIO as GROUP_CHAT_LAUNCH_COUNCIL
from .group_chat_policy_exception_board import SCENARIO as GROUP_CHAT_POLICY_EXCEPTION_BOARD
from .group_chat_quarterly_planning import SCENARIO as GROUP_CHAT_QUARTERLY_PLANNING
from .handoff_claims_exception_routing import SCENARIO as HANDOFF_CLAIMS_EXCEPTION_ROUTING
from .handoff_customer_entitlement import SCENARIO as HANDOFF_CUSTOMER_ENTITLEMENT
from .handoff_support_triage import SCENARIO as HANDOFF_SUPPORT_TRIAGE
from .magentic_business_continuity_drill import SCENARIO as MAGENTIC_BUSINESS_CONTINUITY_DRILL
from .magentic_incident_response import SCENARIO as MAGENTIC_INCIDENT_RESPONSE
from .magentic_supply_chain_disruption import SCENARIO as MAGENTIC_SUPPLY_CHAIN_DISRUPTION
from .sequential_employee_onboarding import SCENARIO as SEQUENTIAL_EMPLOYEE_ONBOARDING
from .sequential_procurement_approval import SCENARIO as SEQUENTIAL_PROCUREMENT_APPROVAL
from .sequential_release_readiness import SCENARIO as SEQUENTIAL_RELEASE_READINESS
from .types import PatternName, ScenarioSpec

SCENARIOS: tuple[ScenarioSpec, ...] = (
    SEQUENTIAL_RELEASE_READINESS,
    CONCURRENT_PR_REVIEW,
    HANDOFF_SUPPORT_TRIAGE,
    GROUP_CHAT_LAUNCH_COUNCIL,
    MAGENTIC_INCIDENT_RESPONSE,
    SEQUENTIAL_EMPLOYEE_ONBOARDING,
    CONCURRENT_VENDOR_RISK_ASSESSMENT,
    HANDOFF_CUSTOMER_ENTITLEMENT,
    GROUP_CHAT_QUARTERLY_PLANNING,
    MAGENTIC_SUPPLY_CHAIN_DISRUPTION,
    SEQUENTIAL_PROCUREMENT_APPROVAL,
    CONCURRENT_SECURITY_ALERT_ENRICHMENT,
    HANDOFF_CLAIMS_EXCEPTION_ROUTING,
    GROUP_CHAT_POLICY_EXCEPTION_BOARD,
    MAGENTIC_BUSINESS_CONTINUITY_DRILL,
)

SCENARIOS_BY_ID: dict[str, ScenarioSpec] = {scenario.id: scenario for scenario in SCENARIOS}
SCENARIO_IDS: tuple[str, ...] = tuple(scenario.id for scenario in SCENARIOS)
PATTERNS: tuple[str, ...] = tuple(dict.fromkeys(scenario.pattern for scenario in SCENARIOS))
PATTERN_DEFAULT_SCENARIO: dict[str, str] = {}
for scenario in SCENARIOS:
    PATTERN_DEFAULT_SCENARIO.setdefault(scenario.pattern, scenario.id)
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
    normalized = (value or "sequential-release-readiness").strip().lower().replace("_", "-")
    normalized = SCENARIO_ALIASES.get(normalized, normalized)
    if normalized not in SCENARIOS_BY_ID:
        raise ValueError(f"Unknown scenario '{value}'. Expected one of: {', '.join(SCENARIO_IDS)}")
    return normalized


def get_scenario(value: str | None) -> ScenarioSpec:
    return SCENARIOS_BY_ID[normalize_scenario_id(value)]


__all__ = [
    "CONCURRENT_PR_REVIEW",
    "CONCURRENT_SECURITY_ALERT_ENRICHMENT",
    "CONCURRENT_VENDOR_RISK_ASSESSMENT",
    "GROUP_CHAT_QUARTERLY_PLANNING",
    "GROUP_CHAT_LAUNCH_COUNCIL",
    "GROUP_CHAT_POLICY_EXCEPTION_BOARD",
    "HANDOFF_CLAIMS_EXCEPTION_ROUTING",
    "HANDOFF_CUSTOMER_ENTITLEMENT",
    "HANDOFF_SUPPORT_TRIAGE",
    "MAGENTIC_BUSINESS_CONTINUITY_DRILL",
    "MAGENTIC_INCIDENT_RESPONSE",
    "MAGENTIC_SUPPLY_CHAIN_DISRUPTION",
    "PATTERN_DEFAULT_SCENARIO",
    "PATTERNS",
    "PatternName",
    "SCENARIO_ALIASES",
    "SCENARIO_IDS",
    "SCENARIOS",
    "SCENARIOS_BY_ID",
    "SEQUENTIAL_EMPLOYEE_ONBOARDING",
    "SEQUENTIAL_PROCUREMENT_APPROVAL",
    "SEQUENTIAL_RELEASE_READINESS",
    "ScenarioSpec",
    "get_scenario",
    "normalize_scenario_id",
]
