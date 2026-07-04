"""Magentic incident automation job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-incident-response",
    pattern="magentic",
    title="Magentic Incident Automation Job",
    learning_goal="Learn how an invocation can carry a custom incident payload into a manager-led dynamic multi-agent workflow.",
    when_to_use="Use Invocations plus magentic orchestration for non-chat jobs that require dynamic planning and specialist coordination.",
    sample_task=(
        "Coordinate an incident job. Timeline: 09:12 export latency p95 doubles; 09:30 the billing "
        "reconciliation job misses its window; 09:41 support tickets spike; 09:55 the exports API "
        "error rate reaches 8 percent. Suspected but unconfirmed: last night's storage driver rollout."
    ),
    agents=(
        AgentSpec("IncidentManagerAgent", "Plans and coordinates the workflow.", "Coordinate the team, select specialists, replan when needed, and produce the final incident result."),
        AgentSpec("TelemetryAnalystAgent", "Analyzes supplied telemetry artifacts.", "Analyze metrics, logs, alerts, and timeline clues from supplied artifacts."),
        AgentSpec("DatabaseSpecialistAgent", "Analyzes database and migration risk.", "Assess database locks, query plans, migrations, and reconciliation job interactions."),
        AgentSpec("InfrastructureSpecialistAgent", "Analyzes platform and capacity risk.", "Assess capacity, queues, network, deployments, and service dependencies."),
        AgentSpec("CustomerImpactAgent", "Analyzes customer impact.", "Estimate customer impact, severity, escalation urgency, and external communication needs."),
        AgentSpec("RemediationPlannerAgent", "Plans mitigation and follow-up.", "Create mitigation, validation, owner handoffs, and prevention follow-up."),
    ),
)
