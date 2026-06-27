"""Magentic incident response scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-incident-response",
    pattern="magentic",
    title="Magentic Incident Response Coordination",
    learning_goal="Learn how a manager agent can dynamically coordinate specialists for a less predictable multi-step response.",
    when_to_use="Use Responses plus magentic orchestration for open-ended tasks that need planning, dynamic specialist selection, and replanning.",
    sample_input="Investigate a production incident where exports are timing out, billing reconciliation is delayed, and support tickets are rising.",
    agents=(
        AgentSpec("IncidentManagerAgent", "Plans and coordinates the incident response.", "Coordinate the team, decide who should act next, replan when blocked, and produce the final incident brief."),
        AgentSpec("TelemetryAnalystAgent", "Analyzes logs, metrics, and symptoms.", "Reason about logs, metrics, alerts, error rates, and timelines from the provided incident description."),
        AgentSpec("CustomerImpactAgent", "Estimates customer and business impact.", "Assess affected customers, severity, communication urgency, and business impact."),
        AgentSpec("MitigationPlannerAgent", "Plans rollback and mitigation options.", "Propose mitigation, rollback, feature-flag, and validation options."),
        AgentSpec("CommsLeadAgent", "Drafts stakeholder and customer communications.", "Draft concise internal updates and customer-safe status language."),
        AgentSpec("PostIncidentReviewerAgent", "Identifies follow-up and prevention work.", "Identify post-incident actions, owners, and prevention themes."),
    ),
)
