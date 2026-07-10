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
    sample_task=(
        "Prepare a release readiness job result before promotion. Scope: the billing reconciliation "
        "nightly job moves to streaming and dashboard exports gain CSV scheduling. Constraints: the "
        "finance close freeze starts Friday, and rollback must not lose reconciliation state."
    ),
    agents=(
        AgentSpec(
            "JobIntakeAgent",
            "Normalizes the incoming job payload.",
            "Normalize the structured invocation into a concise work order: restate the scope items, "
            "the finance-freeze date, and the rollback requirement as explicit checklist entries. "
            "Preserve every supplied field -- later stages build on this work order.",
        ),
        AgentSpec(
            "DependencyAuditAgent",
            "Audits dependencies and rollout sequencing.",
            "Identify dependencies, rollout ordering, migration concerns, and blocked prerequisites "
            "for each scope item in the work order. Call out anything that must land before the "
            "freeze and any ordering the rollback plan forces.",
        ),
        AgentSpec(
            "RiskClassifierAgent",
            "Classifies release-blocking risks.",
            "Classify the release-blocking risks the dependency audit surfaced by severity, "
            "likelihood, owner, and required mitigation. Flag explicitly any risk that violates the "
            "finance-freeze or rollback constraint from the work order.",
        ),
        AgentSpec(
            "EvidenceCheckAgent",
            "Checks evidence and test sufficiency.",
            "Assess whether the supplied artifacts actually support the requested release decision: "
            "name the evidence that exists, the evidence that is missing, and which classified risks "
            "remain unproven either way.",
        ),
        AgentSpec(
            "ActionPlannerAgent",
            "Produces the final action plan.",
            "Synthesize the full pipeline into a release brief: next actions with owners, required "
            "approvals, and a clear go/no-go recommendation that cites the freeze constraint, the "
            "rollback requirement, and the highest-severity risk.",
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
