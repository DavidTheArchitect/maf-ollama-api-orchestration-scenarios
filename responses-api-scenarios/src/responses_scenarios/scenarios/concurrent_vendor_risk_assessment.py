"""Concurrent vendor risk assessment scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-vendor-risk-assessment",
    pattern="concurrent",
    title="Concurrent Vendor Risk Assessment",
    learning_goal="Learn how a Responses API endpoint can fan out one vendor intake question to independent enterprise risk reviewers.",
    when_to_use="Use Responses plus concurrent orchestration when independent departments can assess the same vendor in parallel for a single requester.",
    sample_input=(
        "Assess whether we should approve a new analytics vendor that will process customer usage data "
        "and integrate with our warehouse. Constraints: the annual budget cap is 150k USD, a decision "
        "is needed within two weeks, and the data science team wants API access in the first month."
    ),
    agents=(
        AgentSpec(
            "SecurityRiskAgent",
            "Reviews security controls and access exposure.",
            "Assess identity, encryption, data access, vulnerability management, and "
            "incident-response posture for the analytics vendor. Return your lane's risk rating with "
            "the two facts that most drive it.",
        ),
        AgentSpec(
            "PrivacyRiskAgent",
            "Reviews personal-data and customer-data handling.",
            "Assess data minimization, retention, subprocessors, regional transfer, and "
            "privacy-notice implications of the vendor processing customer usage data. Return your "
            "lane's risk rating and the conditions that would lower it.",
        ),
        AgentSpec(
            "LegalRiskAgent",
            "Reviews contract and liability posture.",
            "Assess indemnity, limitation of liability, audit rights, termination, and compliance "
            "clauses that must be negotiated. Return your lane's risk rating plus the clauses you "
            "would refuse to sign without.",
        ),
        AgentSpec(
            "FinanceRiskAgent",
            "Reviews cost, budget, and renewal exposure.",
            "Assess the pricing model, renewal terms, hidden costs, and fit against the 150k USD "
            "annual budget cap. Return your lane's risk rating and whether the cap survives year-two "
            "renewal pricing.",
        ),
        AgentSpec(
            "OperationsRiskAgent",
            "Reviews supportability and integration readiness.",
            "Assess integration effort against the warehouse integration and the data science team's "
            "first-month deadline, service reliability, support model, monitoring, and fallback. "
            "Return your lane's risk rating and the biggest unknown.",
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
