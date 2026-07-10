"""Group chat launch council scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-launch-council",
    pattern="group-chat",
    title="Group Chat Launch Council",
    learning_goal="Learn how a Responses API chat can expose a collaborative council that iteratively improves an answer, with a closing synthesizer whose verdict ends the discussion.",
    when_to_use="Use Responses plus group chat when transparency, critique, and iterative refinement matter more than a fixed pipeline.",
    sample_input=(
        "Should we launch the new dashboard export feature this week or hold for another beta cohort? "
        "Context: beta feedback is positive but includes two timeout reports, rollback is a feature "
        "flag, and the support docs are still in draft."
    ),
    termination_phrases=("final recommendation",),
    agents=(
        AgentSpec("ProductManagerAgent", "Represents customer value and launch tradeoffs.", "Argue from customer value, scope clarity, launch goals, and business tradeoffs."),
        AgentSpec("SreAgent", "Represents reliability and operations.", "Argue from reliability, observability, rollback, incident risk, and supportability."),
        AgentSpec("SupportLeadAgent", "Represents customer support readiness.", "Argue from support macros, known issues, customer confusion, and escalation burden."),
        AgentSpec("SalesEnablementAgent", "Represents field readiness.", "Argue from customer-facing messaging, enablement, objections, and account-team readiness."),
        AgentSpec(
            "ReleaseNotesAgent",
            "Synthesizes the council and closes each round.",
            "Synthesize the council's positions into release notes, caveats, and internal communications. "
            "When the council has converged, end your turn with a line "
            "'FINAL RECOMMENDATION: <launch or hold> - <one-sentence rationale>'.",
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
