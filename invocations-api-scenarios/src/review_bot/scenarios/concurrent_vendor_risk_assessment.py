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
        "Assess a vendor intake request before procurement approval. Constraints: the annual budget "
        "cap is 150k USD, a decision is needed within two weeks, and the data science team wants API "
        "access in the first month."
    ),
    agents=(
        AgentSpec("SecurityRiskAgent", "Reviews security risk.", "Assess identity, encryption, data access, vulnerability management, and incident-response risk."),
        AgentSpec("PrivacyRiskAgent", "Reviews privacy risk.", "Assess data minimization, retention, subprocessors, regional transfer, and notice implications."),
        AgentSpec("LegalRiskAgent", "Reviews contract risk.", "Assess indemnity, liability, audit rights, termination, and compliance clauses."),
        AgentSpec("FinanceRiskAgent", "Reviews financial risk.", "Assess pricing, renewal terms, hidden costs, budget fit, and procurement risk."),
        AgentSpec("OperationsRiskAgent", "Reviews operational readiness.", "Assess integration effort, service reliability, support model, monitoring, and fallback."),
    ),
)
