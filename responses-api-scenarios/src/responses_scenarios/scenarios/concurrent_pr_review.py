"""Concurrent pull request review scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-pr-review",
    pattern="concurrent",
    title="Concurrent Pull Request Review",
    learning_goal="Learn how a Responses API endpoint can fan out one conversational request to independent expert agents and aggregate their answers.",
    when_to_use="Use Responses plus concurrent orchestration when the user expects one answer but independent perspectives can run in parallel.",
    sample_input=(
        "Review this pull request before the release-branch merge. Diff summary: auth middleware now "
        "caches JWKS keys for 10 minutes (auth/middleware.py, +84/-12); export queries switch from "
        "OFFSET to keyset pagination (exports/query.py, +51/-40); reconciliation tests drop two flaky "
        "cases and add a currency-rounding fixture (tests/test_reconciliation.py, +66/-31)."
    ),
    agents=(
        AgentSpec(
            "SecurityReviewerAgent",
            "Reviews auth, data exposure, and abuse risk.",
            "Review only the security lane: authentication, authorization, secrets, input validation, "
            "and data exposure. The JWKS caching change in auth/middleware.py is yours to judge. "
            "Return a verdict line plus your top findings tied to the diff.",
        ),
        AgentSpec(
            "PerformanceReviewerAgent",
            "Reviews latency and scaling risk.",
            "Review only the performance lane: query cost, batching, memory pressure, concurrency, "
            "and user-visible latency. The OFFSET-to-keyset pagination switch in exports/query.py is "
            "yours to judge. Return a verdict line plus concrete findings.",
        ),
        AgentSpec(
            "TestReviewerAgent",
            "Reviews test coverage and regression risk.",
            "Review only the test lane: whether tests cover the changed behavior, edge cases, "
            "migrations, and rollback behavior. The dropped flaky cases and new currency-rounding "
            "fixture are yours to judge. Return a verdict line plus specific gaps.",
        ),
        AgentSpec(
            "MaintainabilityReviewerAgent",
            "Reviews code clarity and future debugging cost.",
            "Review only the maintainability lane: interfaces, naming, error handling, and "
            "operational debuggability across the three changed files. Return a verdict line plus the "
            "one change most likely to confuse the next engineer.",
        ),
        AgentSpec(
            "ReleaseRiskAgent",
            "Reviews release and rollout risk.",
            "Review only the rollout lane: monitoring, feature flags, customer communications, and "
            "release-blocking risk of merging this change. Return a merge-or-hold verdict line plus "
            "the conditions that would change it.",
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
