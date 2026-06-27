"""Group chat change advisory job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-launch-council",
    pattern="group-chat",
    title="Group Chat Change Advisory Job",
    learning_goal="Learn how an invocation can return a structured result from a transparent multi-agent advisory conversation.",
    when_to_use="Use Invocations plus group chat when an internal system wants a decision record from several named stakeholders.",
    sample_task="Create a change advisory recommendation for launching dashboard export changes this week.",
    agents=(
        AgentSpec("ChangeManagerAgent", "Facilitates the advisory discussion.", "Evaluate change risk, approval criteria, and decision record quality."),
        AgentSpec("SecurityAdvisorAgent", "Represents security constraints.", "Evaluate security and compliance objections or approvals."),
        AgentSpec("ReliabilityAdvisorAgent", "Represents reliability constraints.", "Evaluate SLO, rollback, observability, and operational readiness."),
        AgentSpec("QaAdvisorAgent", "Represents quality gates.", "Evaluate test evidence, regression risk, and release-blocking gaps."),
        AgentSpec("CustomerReadinessAgent", "Represents customer communications.", "Evaluate customer-facing readiness, known issues, and support enablement."),
    ),
)
