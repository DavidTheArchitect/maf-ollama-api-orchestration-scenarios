"""Handoff support triage scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-support-triage",
    pattern="handoff",
    title="Handoff Support Triage",
    learning_goal="Learn how a triage agent names the owning specialist with a ROUTE directive while a code-defined router validates the choice against the allowed routes.",
    when_to_use="Use Responses plus handoff when the right specialist depends on the conversation and the model should pick the owner within a code-validated routing graph.",
    sample_input=(
        "An enterprise admin says invoice exports fail with a 403 immediately after SSO login while "
        "other exports still work, finance close is today, and two more tenants reported the same "
        "error this morning."
    ),
    agents=(
        AgentSpec(
            "SupportTriageAgent",
            "Routes customer issues to the right specialist.",
            "Classify the issue and pick exactly one specialist owner: AuthSpecialistAgent, "
            "BillingSpecialistAgent, DataExportSpecialistAgent, or EscalationCoordinatorAgent. "
            "End your reply with a line 'ROUTE: <AgentName>' naming that specialist.",
        ),
        AgentSpec(
            "AuthSpecialistAgent",
            "Handles login, SSO, and permission problems.",
            "Resolve authentication, SSO, session, permission, and identity-provider concerns.",
            route_keywords=("sso", "login", "auth", "session", "permission", "identity"),
        ),
        AgentSpec(
            "BillingSpecialistAgent",
            "Handles invoices and reconciliation problems.",
            "Resolve invoice, reconciliation, subscription, and finance-close concerns.",
            route_keywords=("invoice", "billing", "reconciliation", "subscription", "finance"),
        ),
        AgentSpec(
            "DataExportSpecialistAgent",
            "Handles dashboard and export failures.",
            "Resolve report export, file format, query, and dashboard data concerns.",
            route_keywords=("export", "dashboard", "report", "file format", "query"),
        ),
        AgentSpec(
            "EscalationCoordinatorAgent",
            "Coordinates urgent escalation and next actions.",
            "Create escalation criteria, next actions, and customer-safe communication for urgent issues.",
            route_keywords=("escalation", "urgent", "outage", "executive", "incident"),
        ),
    ),
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
