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
        "keys for 10 minutes; export queries switch from OFFSET to keyset pagination; reconciliation "
        "tests drop two flaky cases and add a currency-rounding fixture."
    ),
    agents=(
        AgentSpec("SecurityReviewerAgent", "Reviews security risk.", "Review auth, data exposure, secrets, privilege boundaries, and abuse cases."),
        AgentSpec("PerformanceReviewerAgent", "Reviews performance risk.", "Review query cost, concurrency, caching, memory, and throughput risk."),
        AgentSpec("TestReviewerAgent", "Reviews test and regression risk.", "Review coverage, edge cases, failure modes, migrations, and rollback tests."),
        AgentSpec("MaintainabilityReviewerAgent", "Reviews maintainability risk.", "Review readability, interfaces, operational debugging, and future change cost."),
        AgentSpec("ReleaseRiskAgent", "Reviews merge and rollout risk.", "Review release gates, feature flags, monitoring, and customer-impact risk."),
    ),
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
