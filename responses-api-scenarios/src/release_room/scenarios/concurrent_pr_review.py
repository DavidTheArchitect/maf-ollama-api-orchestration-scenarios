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
    sample_input="Review a pull request that changes authentication middleware, export queries, and reconciliation tests before release branch merge.",
    agents=(
        AgentSpec("SecurityReviewerAgent", "Reviews auth, data exposure, and abuse risk.", "Review the change for authentication, authorization, secrets, input validation, and data exposure risk."),
        AgentSpec("PerformanceReviewerAgent", "Reviews latency and scaling risk.", "Review the change for query cost, batching, memory pressure, concurrency, and user-visible latency."),
        AgentSpec("TestReviewerAgent", "Reviews test coverage and regression risk.", "Assess whether tests cover the changed behavior, edge cases, migrations, and rollback behavior."),
        AgentSpec("MaintainabilityReviewerAgent", "Reviews code clarity and future debugging cost.", "Review maintainability, interfaces, naming, error handling, and operational debuggability."),
        AgentSpec("ReleaseRiskAgent", "Reviews release and rollout risk.", "Assess rollout, monitoring, feature flags, customer communications, and release-blocking risk."),
    ),
)
