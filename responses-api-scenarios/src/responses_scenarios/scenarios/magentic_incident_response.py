"""Magentic incident response scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-incident-response",
    pattern="magentic",
    title="Magentic Incident Response Coordination",
    learning_goal="Learn how a manager agent can dynamically coordinate specialists for a less predictable multi-step response.",
    when_to_use="Use Responses plus magentic orchestration for open-ended tasks that need planning, dynamic specialist selection, and replanning.",
    sample_input=(
        "Investigate a production incident. Timeline: 09:12 export latency p95 doubles; 09:30 the "
        "billing reconciliation job misses its window; 09:41 support tickets spike about stuck "
        "dashboard exports; 09:55 the exports API error rate reaches 8 percent. Suspected but "
        "unconfirmed: last night's storage driver rollout. Coordinate the response and produce an "
        "incident brief."
    ),
    agents=(
        AgentSpec(
            "IncidentManagerAgent",
            "Plans and coordinates the incident response.",
            "Coordinate the response: decide who acts next, verify the suspected storage-driver "
            "rollout before committing to mitigation, replan when a finding changes the picture, and "
            "produce the final incident brief with cause, mitigation, and follow-ups.",
        ),
        AgentSpec(
            "TelemetryAnalystAgent",
            "Analyzes logs, metrics, and symptoms.",
            "Reason about the logs, metrics, error rates, and timeline in the incident description. "
            "Establish which symptom came first and whether the sequence supports or contradicts the "
            "storage-driver theory; report evidence, not guesses.",
        ),
        AgentSpec(
            "CustomerImpactAgent",
            "Estimates customer and business impact.",
            "Assess affected customers, severity, communication urgency, and business impact from the "
            "ticket spike and the 8 percent export error rate. Distinguish what customers see now "
            "from what they will see if mitigation waits an hour.",
        ),
        AgentSpec(
            "MitigationPlannerAgent",
            "Plans rollback and mitigation options.",
            "Propose mitigation, rollback, feature-flag, and validation options for the confirmed "
            "cause, each with its blast radius and a verification step. Prefer the option that "
            "restores exports fastest without losing reconciliation state.",
        ),
        AgentSpec(
            "CommsLeadAgent",
            "Drafts stakeholder and customer communications.",
            "Draft the concise internal update and the customer-safe status language for the current "
            "state of the investigation. Keep the external message factual about impact and next "
            "update time without speculating on cause.",
        ),
        AgentSpec(
            "PostIncidentReviewerAgent",
            "Identifies follow-up and prevention work.",
            "Identify the post-incident actions, owners, and prevention themes this timeline suggests "
            "-- especially guardrails that would have caught the storage-driver regression before "
            "rollout. Return a short, assignable list.",
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
