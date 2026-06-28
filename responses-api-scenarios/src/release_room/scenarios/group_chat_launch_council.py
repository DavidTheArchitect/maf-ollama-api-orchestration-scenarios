"""Group chat launch council scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-launch-council",
    pattern="group-chat",
    title="Group Chat Launch Council",
    learning_goal="Learn how a Responses API chat can expose a collaborative council that iteratively improves an answer.",
    when_to_use="Use Responses plus group chat when transparency, critique, and iterative refinement matter more than a fixed pipeline.",
    sample_input="Should we launch the new dashboard export feature this week or hold for another beta cohort?",
    agents=(
        AgentSpec("ProductManagerAgent", "Represents customer value and launch tradeoffs.", "Argue from customer value, scope clarity, launch goals, and business tradeoffs."),
        AgentSpec("SreAgent", "Represents reliability and operations.", "Argue from reliability, observability, rollback, incident risk, and supportability."),
        AgentSpec("SupportLeadAgent", "Represents customer support readiness.", "Argue from support macros, known issues, customer confusion, and escalation burden."),
        AgentSpec("SalesEnablementAgent", "Represents field readiness.", "Argue from customer-facing messaging, enablement, objections, and account-team readiness."),
        AgentSpec("ReleaseNotesAgent", "Represents docs and release communications.", "Turn the discussion into release notes, caveats, and internal communications."),
    ),
)
