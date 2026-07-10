"""Group chat quarterly planning scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-quarterly-planning",
    pattern="group-chat",
    title="Group Chat Quarterly Planning",
    learning_goal="Learn how a Responses API endpoint can expose a multi-stakeholder enterprise planning discussion, with a chief of staff who closes each round and ends the debate with the final plan.",
    when_to_use="Use Responses plus group chat orchestration when a visible debate among business stakeholders improves the final decision.",
    sample_input=(
        "Create a quarterly plan for improving enterprise customer retention while balancing roadmap, "
        "support capacity, sales commitments, and gross margin. Constraint: headcount is frozen this "
        "quarter, so every commitment must trade off against existing capacity."
    ),
    termination_phrases=("final plan",),
    agents=(
        AgentSpec(
            "RevenueLeaderAgent",
            "Represents sales and expansion priorities.",
            "Argue for priorities that improve renewals, expansion, pipeline confidence, and "
            "executive account coverage -- and say what you would give up under the headcount freeze. "
            "Respond to the other leaders' asks rather than restating your own.",
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
            "Synthesizes the council and closes each round.",
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
