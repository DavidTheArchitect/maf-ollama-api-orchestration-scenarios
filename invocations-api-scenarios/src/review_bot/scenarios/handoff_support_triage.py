"""Handoff support triage job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-support-triage",
    pattern="handoff",
    title="Handoff Support Triage Job",
    learning_goal="Learn how a triage agent names the owning specialist with a ROUTE directive while a code-defined router validates the choice, all behind a job-style invocation payload.",
    when_to_use="Use Invocations plus handoff for ticket, webhook, or service-desk automation where the model should pick the owner within a code-validated routing graph.",
    sample_task="Route a support ticket about invoice export failures after SSO login.",
    agents=(
        AgentSpec(
            "TicketTriageAgent",
            "Routes structured support tickets.",
            "Classify the ticket and pick exactly one specialist owner: AuthSpecialistAgent, "
            "BillingSpecialistAgent, ExportSpecialistAgent, or EscalationCoordinatorAgent. "
            "Use the supplied artifacts only. End your reply with a line 'ROUTE: <AgentName>'.",
        ),
        AgentSpec(
            "AuthSpecialistAgent",
            "Handles SSO and permission issues.",
            "Assess SSO, login, session, role, and permission failure modes.",
            route_keywords=("sso", "login", "auth", "session", "permission", "identity"),
        ),
        AgentSpec(
            "BillingSpecialistAgent",
            "Handles invoice and reconciliation issues.",
            "Assess invoices, billing state, reconciliation, and finance-close impact.",
            route_keywords=("invoice", "billing", "reconciliation", "subscription", "finance"),
        ),
        AgentSpec(
            "ExportSpecialistAgent",
            "Handles export and report failures.",
            "Assess export queries, formats, dashboard state, and data pipeline issues.",
            route_keywords=("export", "dashboard", "report", "file format", "query"),
        ),
        AgentSpec(
            "EscalationCoordinatorAgent",
            "Plans escalation and communications.",
            "Create escalation actions, owner handoffs, and customer-safe communication.",
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
