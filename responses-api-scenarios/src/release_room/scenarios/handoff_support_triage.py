"""Handoff support triage scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-support-triage",
    pattern="handoff",
    title="Handoff Support Triage",
    learning_goal="Learn how a conversational Responses API session can route turns between specialists while keeping the public protocol unchanged.",
    when_to_use="Use Responses plus handoff when the user may ask follow-ups and the right specialist depends on the conversation.",
    sample_input="A customer says their invoice export fails after SSO login and they need an answer before finance close.",
    agents=(
        AgentSpec("SupportTriageAgent", "Routes customer issues to the right specialist.", "Classify the issue and hand off to the most relevant specialist. Ask clarifying questions only when needed."),
        AgentSpec("AuthSpecialistAgent", "Handles login, SSO, and permission problems.", "Resolve authentication, SSO, session, permission, and identity-provider concerns."),
        AgentSpec("BillingSpecialistAgent", "Handles invoices and reconciliation problems.", "Resolve invoice, reconciliation, subscription, and finance-close concerns."),
        AgentSpec("DataExportSpecialistAgent", "Handles dashboard and export failures.", "Resolve report export, file format, query, and dashboard data concerns."),
        AgentSpec("EscalationCoordinatorAgent", "Coordinates urgent escalation and next actions.", "Create escalation criteria, next actions, and customer-safe communication for urgent issues."),
    ),
)
