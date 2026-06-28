"""Handoff support triage job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-support-triage",
    pattern="handoff",
    title="Handoff Support Triage Job",
    learning_goal="Learn how an invocation can still manage session-aware routing while owning its own JSON payload.",
    when_to_use="Use Invocations plus handoff for ticket, webhook, or service-desk automation that routes to specialists.",
    sample_task="Route a support ticket about invoice export failures after SSO login.",
    agents=(
        AgentSpec("TicketTriageAgent", "Routes structured support tickets.", "Classify the ticket and hand off to the best specialist. Use the supplied artifacts only."),
        AgentSpec("AuthSpecialistAgent", "Handles SSO and permission issues.", "Assess SSO, login, session, role, and permission failure modes."),
        AgentSpec("BillingSpecialistAgent", "Handles invoice and reconciliation issues.", "Assess invoices, billing state, reconciliation, and finance-close impact."),
        AgentSpec("ExportSpecialistAgent", "Handles export and report failures.", "Assess export queries, formats, dashboard state, and data pipeline issues."),
        AgentSpec("EscalationCoordinatorAgent", "Plans escalation and communications.", "Create escalation actions, owner handoffs, and customer-safe communication."),
    ),
)
