"""Group chat quarterly planning job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-quarterly-planning",
    pattern="group-chat",
    title="Group Chat Quarterly Planning Job",
    learning_goal="Learn how an invocation can return a structured decision record from an internal enterprise planning council.",
    when_to_use="Use Invocations plus group chat orchestration for planning jobs that need stakeholder critique before producing a record.",
    sample_task="Produce a quarterly operating plan recommendation from stakeholder inputs.",
    agents=(
        AgentSpec("RevenueLeaderAgent", "Represents sales and expansion priorities.", "Argue for renewals, expansion, pipeline confidence, and executive account coverage."),
        AgentSpec("ProductLeaderAgent", "Represents roadmap and delivery tradeoffs.", "Argue for product bets, sequencing, capacity limits, and customer-impact tradeoffs."),
        AgentSpec("SupportLeaderAgent", "Represents support load and customer health.", "Argue for supportability, ticket reduction, knowledge gaps, and escalation capacity."),
        AgentSpec("FinanceLeaderAgent", "Represents budget and margin discipline.", "Argue for gross margin, headcount, spend controls, and measurable business outcomes."),
        AgentSpec("ChiefOfStaffAgent", "Synthesizes the planning council.", "Drive convergence toward a practical quarterly plan with owners, metrics, and explicit tradeoffs."),
    ),
)
