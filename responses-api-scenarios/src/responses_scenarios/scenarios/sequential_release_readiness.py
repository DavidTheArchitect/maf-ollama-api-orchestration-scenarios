"""Sequential release readiness scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-release-readiness",
    pattern="sequential",
    title="Sequential Release Readiness Pipeline",
    learning_goal="Learn how Responses API clients can send a normal chat request while the server runs a fixed multi-stage agent pipeline.",
    when_to_use="Use Responses plus sequential orchestration when each turn should produce a conversational answer through a predictable chain of review stages.",
    sample_input=(
        "Prepare a release readiness brief for version 2.4.0. Scope: (1) the billing reconciliation "
        "nightly job moves to streaming, (2) dashboard exports gain CSV scheduling, (3) API fixes for "
        "pagination and rate-limit headers. Constraints: the finance close freeze starts Friday, and "
        "rollback must not lose reconciliation state."
    ),
    agents=(
        AgentSpec(
            "ScopePlannerAgent",
            "Extracts release scope and readiness questions.",
            "Turn the user request into a concrete release-scope summary and an ordered list of "
            "readiness questions the later stages must answer. Restate the scope items and "
            "constraints explicitly -- the whole pipeline builds on this summary.",
        ),
        AgentSpec(
            "DependencyPlannerAgent",
            "Identifies dependencies and sequencing.",
            "Identify upstream and downstream teams, rollout dependencies, migration needs, and "
            "sequencing constraints for each scope item the planner listed. Call out anything that "
            "must land before the finance-close freeze.",
        ),
        AgentSpec(
            "RiskReviewerAgent",
            "Reviews operational and customer risk.",
            "Assess operational risk, rollback risk, security exposure, and customer impact for the "
            "dependencies identified so far. Return each risk with severity, likelihood, and a "
            "concrete mitigation -- flag anything that threatens the freeze or rollback constraint.",
        ),
        AgentSpec(
            "DocsWriterAgent",
            "Plans release notes and internal docs.",
            "Create release-note bullets, internal enablement tasks, and support-facing documentation "
            "needs grounded in the actual scope and risks above, not generic boilerplate. Note which "
            "docs are release-blocking.",
        ),
        AgentSpec(
            "FinalEditorAgent",
            "Creates the final readiness brief.",
            "Synthesize the prior stages into the final readiness brief: scope, top risks with "
            "mitigations, required follow-ups with owners, and a go/no-go recommendation that cites "
            "the freeze and rollback constraints.",
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
