"""Handoff customer entitlement job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-customer-entitlement",
    pattern="handoff",
    title="Handoff Customer Entitlement Job",
    learning_goal="Learn how an invocation can route a structured customer entitlement case to the right enterprise specialist.",
    when_to_use="Use Invocations plus handoff orchestration for CRM, support, or account workflows where ownership depends on case context.",
    sample_task="Route and resolve a customer entitlement case.",
    agents=(
        AgentSpec("EntitlementTriageAgent", "Classifies and routes entitlement cases.", "Determine whether the issue is commercial, billing, support, product, or engineering owned, then hand off to the best specialist."),
        AgentSpec("BillingOpsAgent", "Reviews billing state.", "Assess renewal, invoice, payment, SKU, and subscription-status explanations for entitlement loss."),
        AgentSpec("ContractOpsAgent", "Reviews contract terms.", "Assess order form terms, purchased modules, amendments, and account exceptions."),
        AgentSpec("CustomerSupportAgent", "Plans support response.", "Prepare customer-safe communication, workaround options, escalation notes, and case updates."),
        AgentSpec("ProductEngineeringAgent", "Reviews entitlement systems.", "Assess feature flags, provisioning jobs, entitlement service defects, and remediation steps."),
    ),
)
