"""Concurrent pull request review job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-pr-review",
    pattern="concurrent",
    title="Concurrent Pull Request Review Job",
    learning_goal="Learn how an invocation can fan out a structured review payload to multiple independent reviewers.",
    when_to_use="Use Invocations plus concurrent orchestration for CI, webhook, and batch reviews where each expert can run independently.",
    sample_task=(
        "Review this PR before the release-branch merge. Diff summary: auth middleware caches JWKS "
        "keys for 10 minutes (auth/middleware.py, +84/-12); export queries switch from OFFSET to "
        "keyset pagination (exports/query.py, +51/-40); reconciliation tests drop two flaky cases "
        "and add a currency-rounding fixture (tests/test_reconciliation.py, +66/-31)."
    ),
    agents=(
        AgentSpec(
            "SecurityReviewerAgent",
            "Reviews security risk.",
            "Review only the security lane of the diff: authentication, data exposure, secrets, "
            "privilege boundaries, and abuse cases. The JWKS caching change is yours to judge. Return "
            "a verdict line plus your top findings, not generic advice.",
        ),
        AgentSpec(
            "PerformanceReviewerAgent",
            "Reviews performance risk.",
            "Review only the performance lane: query cost, concurrency, caching, memory, and "
            "throughput. The pagination switch from OFFSET to keyset is yours to judge. Return a "
            "verdict line plus concrete findings tied to the diff.",
        ),
        AgentSpec(
            "TestReviewerAgent",
            "Reviews test and regression risk.",
            "Review only the test lane: coverage of changed behavior, edge cases, failure modes, "
            "migrations, and rollback tests. The dropped flaky cases and the new currency-rounding "
            "fixture are yours to judge. Return a verdict line plus specific gaps.",
        ),
        AgentSpec(
            "MaintainabilityReviewerAgent",
            "Reviews maintainability risk.",
            "Review only the maintainability lane: readability, interface design, operational "
            "debugging, and future change cost across the three changed areas. Return a verdict line "
            "plus the one change most likely to confuse the next engineer.",
        ),
        AgentSpec(
            "ReleaseRiskAgent",
            "Reviews merge and rollout risk.",
            "Review only the rollout lane: release gates, feature flags, monitoring, and customer-"
            "impact risk of merging this diff to the release branch. Return a merge-or-hold verdict "
            "line plus the conditions that would change it.",
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
