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
        AgentSpec("ScopePlannerAgent", "Extracts release scope and readiness questions.", "Turn the user request into a concrete release-scope summary and ordered readiness questions."),
        AgentSpec("DependencyPlannerAgent", "Identifies dependencies and sequencing.", "Identify upstream/downstream teams, rollout dependencies, migration needs, and sequencing constraints."),
        AgentSpec("RiskReviewerAgent", "Reviews operational and customer risk.", "Assess operational risk, rollback risk, security exposure, and customer impact. Return mitigations."),
        AgentSpec("DocsWriterAgent", "Plans release notes and internal docs.", "Create release-note bullets, internal enablement tasks, and support-facing docs needs."),
        AgentSpec("FinalEditorAgent", "Creates the final readiness brief.", "Synthesize the prior outputs into scope, risks, required follow-ups, and a go/no-go recommendation."),
    ),
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
