"""Concurrent vendor risk assessment job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-vendor-risk-assessment",
    pattern="concurrent",
    title="Concurrent Vendor Risk Assessment Job",
    learning_goal="Learn how an invocation can fan out a structured vendor intake payload to independent enterprise risk reviewers.",
    when_to_use="Use Invocations plus concurrent orchestration for procurement, GRC, or vendor-intake workflows with independent review dimensions.",
    sample_task=(
        "Assess an intake request for a usage-analytics vendor that will process customer usage data "
        "and integrate with the warehouse. Constraints: the annual budget cap is 150k USD, a decision "
        "is needed within two weeks, and the data science team wants API access in the first month."
    ),
    agents=(
        AgentSpec(
            "SecurityRiskAgent",
            "Reviews security risk.",
            "Assess identity, encryption, data access, vulnerability management, and incident-"
            "response posture for the proposed vendor. Return your lane's risk rating with the two "
            "facts that most drive it.",
        ),
        AgentSpec(
            "PrivacyRiskAgent",
            "Reviews privacy risk.",
            "Assess data minimization, retention, subprocessors, regional transfer, and notice "
            "implications of the vendor processing customer usage data. Return your lane's risk "
            "rating and any conditions that would lower it.",
        ),
        AgentSpec(
            "LegalRiskAgent",
            "Reviews contract risk.",
            "Assess indemnity, liability caps, audit rights, termination, and compliance clauses that "
            "must be negotiated. Return your lane's risk rating plus the clauses you would refuse to "
            "sign without.",
        ),
        AgentSpec(
            "FinanceRiskAgent",
            "Reviews financial risk.",
            "Assess pricing, renewal terms, hidden costs, and fit against the 150k USD annual budget "
            "cap. Return your lane's risk rating and whether the cap survives year-two renewal "
            "pricing.",
        ),
        AgentSpec(
            "OperationsRiskAgent",
            "Reviews operational readiness.",
            "Assess integration effort against the data science team's first-month API deadline, "
            "service reliability, support model, monitoring, and fallback. Return your lane's risk "
            "rating and the biggest operational unknown.",
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
