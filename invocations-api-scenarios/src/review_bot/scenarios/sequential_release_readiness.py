"""Sequential release readiness job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-release-readiness",
    pattern="sequential",
    title="Sequential Release Readiness Job",
    learning_goal="Learn how an invocation can accept a structured job and run a deterministic multi-stage review pipeline.",
    when_to_use="Use Invocations plus sequential orchestration for webhook or CI jobs that must pass through fixed processing stages.",
    sample_task="Prepare a release readiness job result for a billing reconciliation change before promotion.",
    agents=(
        AgentSpec("JobIntakeAgent", "Normalizes the incoming job payload.", "Normalize the structured invocation into a concise work order. Preserve supplied fields."),
        AgentSpec("DependencyAuditAgent", "Audits dependencies and rollout sequencing.", "Identify dependencies, rollout ordering, migration concerns, and blocked prerequisites."),
        AgentSpec("RiskClassifierAgent", "Classifies release-blocking risks.", "Classify risks by severity, likelihood, owner, and required mitigation."),
        AgentSpec("EvidenceCheckAgent", "Checks evidence and test sufficiency.", "Assess whether supplied artifacts support the requested release decision."),
        AgentSpec("ActionPlannerAgent", "Produces the final action plan.", "Synthesize the pipeline into next actions, required approvals, and a release recommendation."),
    ),
)
