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
    sample_task=(
        "Route urgent ticket 10492: an enterprise admin reports invoice exports fail with a 403 "
        "immediately after SSO login while other exports still work, finance close is today, and two "
        "more tenants reported the same error this morning."
    ),
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
            "Diagnose the SSO, login, session, role, and permission failure modes the ticket "
            "describes. State the most likely cause, the fastest verification step, and a customer-"
            "safe next reply the support team can send today.",
            route_keywords=("sso", "login", "auth", "session", "permission", "identity"),
        ),
        AgentSpec(
            "BillingSpecialistAgent",
            "Handles invoice and reconciliation issues.",
            "Diagnose the invoice, billing-state, and reconciliation angles of the ticket, including "
            "finance-close impact. State the most likely cause, what to check in billing state, and a "
            "customer-safe next reply.",
            route_keywords=("invoice", "billing", "reconciliation", "subscription", "finance"),
        ),
        AgentSpec(
            "ExportSpecialistAgent",
            "Handles export and report failures.",
            "Diagnose the export-query, file-format, dashboard-state, and data-pipeline angles of the "
            "ticket. State the most likely cause, the fastest reproduction step, and a customer-safe "
            "next reply.",
            route_keywords=("export", "dashboard", "report", "file format", "query"),
        ),
        AgentSpec(
            "EscalationCoordinatorAgent",
            "Plans escalation and communications.",
            "Plan the escalation: severity call, owner handoffs, timeline given the finance-close "
            "deadline, and a customer-safe communication. Multiple tenants reporting the same error "
            "is your signal to treat this as a potential incident.",
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
