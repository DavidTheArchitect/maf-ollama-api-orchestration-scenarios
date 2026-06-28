"""Handoff customer entitlement scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-customer-entitlement",
    pattern="handoff",
    title="Handoff Customer Entitlement",
    learning_goal="Learn how a Responses API conversation can route a customer entitlement issue to the right enterprise specialist.",
    when_to_use="Use Responses plus handoff orchestration when a customer-facing conversation may need billing, contract, support, or engineering ownership.",
    sample_input="A strategic customer says their purchased premium reporting feature disappeared after renewal, and the account team needs a same-day answer.",
    agents=(
        AgentSpec("EntitlementTriageAgent", "Classifies the entitlement issue and routes work.", "Determine whether the issue is commercial, billing, support, product, or engineering owned, then hand off to the best specialist."),
        AgentSpec("BillingOpsAgent", "Reviews invoicing and subscription state.", "Assess renewal, invoice, payment, SKU, and subscription-status explanations for entitlement loss."),
        AgentSpec("ContractOpsAgent", "Reviews order form and commercial terms.", "Assess contract terms, purchased modules, renewal amendments, and account exceptions."),
        AgentSpec("CustomerSupportAgent", "Plans customer communication and workaround.", "Prepare customer-safe communication, case updates, workaround options, and escalation notes."),
        AgentSpec("ProductEngineeringAgent", "Reviews product flags and entitlement services.", "Assess feature flags, provisioning jobs, entitlement service defects, and remediation steps."),
    ),
)
