"""Handoff customer entitlement job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-customer-entitlement",
    pattern="handoff",
    title="Handoff Customer Entitlement Job",
    learning_goal="Learn how a triage agent names the owning enterprise specialist with a ROUTE directive that a code-defined router validates before handing off the entitlement case.",
    when_to_use="Use Invocations plus handoff orchestration for CRM, support, or account workflows where ownership depends on case context and the model should name the owner.",
    sample_task="Route and resolve a customer entitlement case.",
    agents=(
        AgentSpec(
            "EntitlementTriageAgent",
            "Classifies and routes entitlement cases.",
            "Determine whether the issue is billing, contract, support, or engineering owned: "
            "BillingOpsAgent, ContractOpsAgent, CustomerSupportAgent, or ProductEngineeringAgent. "
            "End your reply with a line 'ROUTE: <AgentName>' naming that owner.",
        ),
        AgentSpec(
            "BillingOpsAgent",
            "Reviews billing state.",
            "Assess renewal, invoice, payment, SKU, and subscription-status explanations for entitlement loss.",
            route_keywords=("invoice", "billing", "subscription", "renewal", "payment"),
        ),
        AgentSpec(
            "ContractOpsAgent",
            "Reviews contract terms.",
            "Assess order form terms, purchased modules, amendments, and account exceptions.",
            route_keywords=("contract", "order form", "terms", "amendment", "commercial"),
        ),
        AgentSpec(
            "CustomerSupportAgent",
            "Plans support response.",
            "Prepare customer-safe communication, workaround options, escalation notes, and case updates.",
            route_keywords=("communication", "workaround", "case update", "apology"),
        ),
        AgentSpec(
            "ProductEngineeringAgent",
            "Reviews entitlement systems.",
            "Assess feature flags, provisioning jobs, entitlement service defects, and remediation steps.",
            route_keywords=("feature flag", "provisioning", "entitlement service", "defect", "engineering"),
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
