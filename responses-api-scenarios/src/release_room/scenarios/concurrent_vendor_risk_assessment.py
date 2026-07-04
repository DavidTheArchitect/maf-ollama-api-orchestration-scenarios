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
        AgentSpec("SecurityRiskAgent", "Reviews security controls and access exposure.", "Assess identity, encryption, data access, vulnerability management, and incident-response risk."),
        AgentSpec("PrivacyRiskAgent", "Reviews personal-data and customer-data handling.", "Assess data minimization, retention, subprocessors, regional transfer, and privacy notice implications."),
        AgentSpec("LegalRiskAgent", "Reviews contract and liability posture.", "Assess indemnity, limitation of liability, audit rights, termination, and compliance clauses."),
        AgentSpec("FinanceRiskAgent", "Reviews cost, budget, and renewal exposure.", "Assess pricing model, renewal terms, hidden costs, budget fit, and procurement risk."),
        AgentSpec("OperationsRiskAgent", "Reviews supportability and integration readiness.", "Assess integration effort, service reliability, support model, monitoring, and operational fallback."),
    ),
)
