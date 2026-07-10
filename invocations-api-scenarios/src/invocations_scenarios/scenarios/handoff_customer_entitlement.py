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
    sample_task=(
        "Route and resolve entitlement case 88421: Contoso, a strategic account, lost access to its "
        "purchased premium reporting feature after last week's plan renewal, billing shows the "
        "subscription as active, and the account team needs a same-day answer."
    ),
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
            "Assess the renewal, invoice, payment, SKU, and subscription-status explanations for the "
            "entitlement loss. Billing shows the subscription active, so explain what else in billing "
            "state could drop a feature; return a diagnosis and the fix path you own.",
            route_keywords=("invoice", "billing", "subscription", "renewal", "payment"),
        ),
        AgentSpec(
            "ContractOpsAgent",
            "Reviews contract terms.",
            "Assess the order form terms, purchased modules, amendments, and account-specific "
            "exceptions. The contract shows premium reporting included through year-end -- confirm "
            "what the entitlement should be and produce the evidence the account team can cite.",
            route_keywords=("contract", "order form", "terms", "amendment", "commercial"),
        ),
        AgentSpec(
            "CustomerSupportAgent",
            "Plans support response.",
            "Prepare the customer-safe communication for a strategic account on a same-day clock: "
            "what happened, the workaround if any, the fix timeline, and internal case notes with the "
            "escalation path.",
            route_keywords=("communication", "workaround", "case update", "apology"),
        ),
        AgentSpec(
            "ProductEngineeringAgent",
            "Reviews entitlement systems.",
            "Assess feature flags, provisioning jobs, and entitlement-service defects that could drop "
            "a purchased feature after renewal. Name the most likely mechanism, the verification "
            "query, and the remediation steps.",
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
