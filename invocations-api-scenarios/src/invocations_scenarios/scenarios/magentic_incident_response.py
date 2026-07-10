"""Magentic incident automation job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-incident-response",
    pattern="magentic",
    title="Magentic Incident Response Job",
    learning_goal="Learn how an invocation can carry a custom incident payload into a manager-led dynamic multi-agent workflow.",
    when_to_use="Use Invocations plus magentic orchestration for non-chat jobs that require dynamic planning and specialist coordination.",
    sample_task=(
        "Coordinate an incident job. Timeline: 09:12 export latency p95 doubles; 09:30 the billing "
        "reconciliation job misses its window; 09:41 support tickets spike; 09:55 the exports API "
        "error rate reaches 8 percent. Suspected but unconfirmed: last night's storage driver rollout."
    ),
    agents=(
        AgentSpec(
            "IncidentManagerAgent",
            "Plans and coordinates the workflow.",
            "Coordinate the investigation: sequence the specialists, verify the suspected storage-"
            "driver cause before committing to mitigation, replan when a finding changes the picture, "
            "and produce the final incident result with cause, mitigation, and follow-ups.",
        ),
        AgentSpec(
            "TelemetryAnalystAgent",
            "Analyzes supplied telemetry artifacts.",
            "Analyze the metrics, logs, alerts, and timeline clues in the supplied artifacts. "
            "Establish which symptom came first and whether the timeline supports or contradicts the "
            "storage-driver theory; report evidence, not guesses.",
        ),
        AgentSpec(
            "DatabaseSpecialistAgent",
            "Analyzes database and migration risk.",
            "Assess database locks, query plans, migrations, and the reconciliation job's interaction "
            "with storage. State clearly whether the database layer is a cause, a victim, or "
            "unaffected, and cite the timeline facts you rely on.",
        ),
        AgentSpec(
            "InfrastructureSpecialistAgent",
            "Analyzes platform and capacity risk.",
            "Assess capacity, queues, network, recent deployments, and service dependencies -- "
            "especially last night's storage driver rollout. Report what verification would confirm "
            "or clear it and the fastest safe mitigation.",
        ),
        AgentSpec(
            "CustomerImpactAgent",
            "Analyzes customer impact.",
            "Estimate customer impact from the ticket spike and the 8 percent export error rate: "
            "affected segments, severity, escalation urgency, and what external communication is "
            "needed now versus after mitigation.",
        ),
        AgentSpec(
            "RemediationPlannerAgent",
            "Plans mitigation and follow-up.",
            "Create the mitigation and follow-up plan: immediate mitigation with a validation step, "
            "owner handoffs, and prevention actions. Tie each item to a confirmed finding from the "
            "investigation, not to the initial suspicion.",
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
