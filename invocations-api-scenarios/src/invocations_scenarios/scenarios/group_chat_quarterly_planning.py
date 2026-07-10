"""Group chat quarterly planning job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-quarterly-planning",
    pattern="group-chat",
    title="Group Chat Quarterly Planning Job",
    learning_goal="Learn how an invocation can return a structured decision record from an internal enterprise planning council, with a chief of staff who closes each round and ends the debate with the final plan.",
    when_to_use="Use Invocations plus group chat orchestration for planning jobs that need stakeholder critique before producing a record.",
    sample_task=(
        "Produce a quarterly operating plan focused on improving enterprise customer retention. "
        "Constraint: headcount is frozen this quarter, so every commitment must trade off against "
        "existing capacity and name what it displaces."
    ),
    termination_phrases=("final plan",),
    agents=(
        AgentSpec(
            "RevenueLeaderAgent",
            "Represents sales and expansion priorities.",
            "Argue for renewals, expansion, pipeline confidence, and executive account coverage -- "
            "and say what you would give up under the headcount freeze. Respond to the other leaders' "
            "asks rather than restating your own.",
        ),
        AgentSpec(
            "ProductLeaderAgent",
            "Represents roadmap and delivery tradeoffs.",
            "Argue for product bets, sequencing, and capacity limits, making the customer-impact "
            "tradeoffs explicit. Under the freeze, every bet you propose must name what it displaces; "
            "challenge asks that ignore capacity.",
        ),
        AgentSpec(
            "SupportLeaderAgent",
            "Represents support load and customer health.",
            "Argue for supportability, ticket reduction, knowledge gaps, and escalation capacity. "
            "Quantify what current load makes impossible this quarter and negotiate directly with the "
            "commitments the other leaders propose.",
        ),
        AgentSpec(
            "FinanceLeaderAgent",
            "Represents budget and margin discipline.",
            "Argue for gross margin, spend controls, and measurable outcomes under the frozen "
            "headcount. Ask the other leaders for the numbers behind their asks and flag any "
            "commitment with no measurable exit criterion.",
        ),
        AgentSpec(
            "ChiefOfStaffAgent",
            "Synthesizes the planning council and closes each round.",
            "Drive convergence toward a practical quarterly plan with owners, metrics, and explicit tradeoffs. "
            "When the council has converged, end your turn with a line 'FINAL PLAN:' followed by the plan summary.",
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
