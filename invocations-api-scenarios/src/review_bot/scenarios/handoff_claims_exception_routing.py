"""Handoff claims exception routing job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-claims-exception-routing",
    pattern="handoff",
    title="Handoff Claims Exception Routing Job",
    learning_goal="Learn how a triage agent grounds the routing decision in MCP facts, names the owner with a ROUTE directive, and how the routed specialist's decision always flows to a customer-communication finisher.",
    when_to_use="Use Invocations plus handoff orchestration when the correct owner of a claim exception job depends on tool-grounded facts and every outcome must end with a customer communication.",
    sample_task="Run a claims exception routing job for CLAIM-88120 (water damage, exceeds auto-approval) and explain the routing decision.",
    handoff_finisher="CustomerCommsAgent",
    agents=(
        AgentSpec(
            "ClaimTriageAgent",
            "Classifies and routes the claim exception.",
            "Decide which specialist should own the claim: PaymentSpecialistAgent, FraudSpecialistAgent, "
            "or ComplianceSpecialistAgent. Use lookup_enterprise_record for the claim and "
            "calculate_priority_score to rank it. Per policy POL-CLM-09, any fraud signal routes to "
            "FraudSpecialistAgent before payment is considered; a compliance hold routes to "
            "ComplianceSpecialistAgent. End your reply with a line 'ROUTE: <AgentName>'.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "PaymentSpecialistAgent",
            "Handles payment release exceptions.",
            "Decide whether and how to release payment. Use search_policy to ground the auto-approval threshold and exception handling.",
            mcp_tools=("search_policy",),
            route_keywords=("payment", "release", "threshold", "approval"),
        ),
        AgentSpec(
            "FraudSpecialistAgent",
            "Investigates fraud signals.",
            "Investigate fraud indicators on the claim. Use lookup_enterprise_record and search_policy to assess the fraud signal and required steps.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
            route_keywords=("fraud", "signal", "mismatched", "investigation"),
        ),
        AgentSpec(
            "ComplianceSpecialistAgent",
            "Checks compliance holds.",
            "Determine whether a compliance hold applies. Use search_policy to ground the claim exception routing policy.",
            mcp_tools=("search_policy",),
            route_keywords=("compliance", "hold", "regulatory"),
        ),
        AgentSpec(
            "CustomerCommsAgent",
            "Drafts the customer communication.",
            "You receive the routed specialist's decision. Draft a clear, empathetic customer message for it. Use create_decision_log_entry to record the communicated outcome.",
            mcp_tools=("create_decision_log_entry",),
        ),
    ),
)
