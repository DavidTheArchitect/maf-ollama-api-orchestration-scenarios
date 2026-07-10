"""Group chat change advisory job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-launch-council",
    pattern="group-chat",
    title="Group Chat Launch Council Job",
    learning_goal="Learn how an invocation can return a structured result from a transparent multi-agent advisory conversation, with a facilitator whose verdict closes the discussion.",
    when_to_use="Use Invocations plus group chat when an internal system wants a decision record from several named stakeholders.",
    sample_task=(
        "Create a change advisory recommendation for launching dashboard export changes this week. "
        "Context: beta cohort feedback is positive but includes two timeout reports, rollback is a "
        "feature flag, and the support docs are still in draft."
    ),
    termination_phrases=("final recommendation",),
    agents=(
        AgentSpec(
            "SecurityAdvisorAgent",
            "Represents security constraints.",
            "Argue the security and compliance position on the launch: data exposure of scheduled "
            "exports, audit impact, and any approval conditions. React to the other advisors' points "
            "rather than restating your opening position.",
        ),
        AgentSpec(
            "ReliabilityAdvisorAgent",
            "Represents reliability constraints.",
            "Argue the reliability position: what the two timeout reports imply, whether the feature-"
            "flag rollback is a real safety net, and what observability must exist before launch. "
            "Respond to the other advisors' arguments directly.",
        ),
        AgentSpec(
            "QaAdvisorAgent",
            "Represents quality gates.",
            "Argue the quality position: what the beta evidence does and does not prove, which "
            "regression risks remain, and what would be release-blocking. Challenge or concede the "
            "other advisors' claims explicitly.",
        ),
        AgentSpec(
            "CustomerReadinessAgent",
            "Represents customer communications.",
            "Argue the customer-facing position: draft-only support docs, known-issue messaging, and "
            "support enablement gaps. Say concretely what must ship with the feature and what can "
            "follow, responding to the debate so far.",
        ),
        AgentSpec(
            "ChangeManagerAgent",
            "Facilitates the advisory discussion and closes each round.",
            "Evaluate change risk, approval criteria, and decision record quality. When the advisors have "
            "converged, end your turn with a line 'FINAL RECOMMENDATION: <approve or hold> - <one-sentence rationale>'.",
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
