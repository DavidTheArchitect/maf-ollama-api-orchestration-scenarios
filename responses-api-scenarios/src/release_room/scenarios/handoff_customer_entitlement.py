"""Handoff customer entitlement scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-customer-entitlement",
    pattern="handoff",
    title="Handoff Customer Entitlement",
    learning_goal="Learn how a triage agent names the owning enterprise specialist with a ROUTE directive that a code-defined router validates before handing off the entitlement issue.",
    when_to_use="Use Responses plus handoff orchestration when a customer-facing conversation may need billing, contract, support, or engineering ownership and the model should name the owner.",
    sample_input="A strategic customer says their purchased premium reporting feature disappeared after renewal, and the account team needs a same-day answer.",
    agents=(
        AgentSpec(
            "EntitlementTriageAgent",
            "Classifies the entitlement issue and routes work.",
            "Determine whether the issue is billing, contract, support, or engineering owned: "
            "BillingOpsAgent, ContractOpsAgent, CustomerSupportAgent, or ProductEngineeringAgent. "
            "End your reply with a line 'ROUTE: <AgentName>' naming that owner.",
        ),
        AgentSpec(
            "BillingOpsAgent",
            "Reviews invoicing and subscription state.",
            "Assess renewal, invoice, payment, SKU, and subscription-status explanations for entitlement loss.",
            route_keywords=("invoice", "billing", "subscription", "renewal", "payment"),
        ),
        AgentSpec(
            "ContractOpsAgent",
            "Reviews order form and commercial terms.",
            "Assess contract terms, purchased modules, renewal amendments, and account exceptions.",
            route_keywords=("contract", "order form", "terms", "amendment", "commercial"),
        ),
        AgentSpec(
            "CustomerSupportAgent",
            "Plans customer communication and workaround.",
            "Prepare customer-safe communication, case updates, workaround options, and escalation notes.",
            route_keywords=("communication", "workaround", "case update", "apology"),
        ),
        AgentSpec(
            "ProductEngineeringAgent",
            "Reviews product flags and entitlement services.",
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
