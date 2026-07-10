"""Sequential loan origination job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-loan-origination",
    pattern="sequential",
    title="Sequential Loan Origination Job",
    learning_goal="Learn why a regulated underwriting pipeline is the canonical sequential use case: every application walks the same intake, credit, income, pricing, and offer stages in a fixed order, and each stage builds on tool-grounded facts from the one before it.",
    when_to_use="Use Invocations plus sequential orchestration for lending jobs where the stage order is mandated by policy and skipping or reordering a check is a compliance failure, not an optimization.",
    sample_task="Run a loan origination job for application LOAN-73021 (home purchase mortgage) and return an offer packet with a pricing decision.",
    agents=(
        AgentSpec(
            "ApplicationIntakeAgent",
            "Normalizes the loan application.",
            "Turn the job into a concrete underwriting work order. Use lookup_enterprise_record to pull the application and restate the amount, credit score, debt-to-income ratio, loan-to-value ratio, and employment history.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "CreditAnalysisAgent",
            "Assesses the credit profile.",
            "Assess the applicant's credit profile against lending policy. Use search_policy for the manual underwriting referral rules and state clearly whether the credit score alone triggers a referral.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "IncomeVerificationAgent",
            "Verifies income and recomputes ratios.",
            "Verify the income basis and confirm the debt-to-income ratio from the prior stages. Use lookup_enterprise_record to re-check the application figures and calculate_priority_score to rank how much scrutiny the file needs.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "RiskPricingAgent",
            "Prices the risk tier or refers the file.",
            "Price the loan into a risk tier, or refer it for manual underwriting when the ratios exceed the referral limits. Use search_policy to ground the referral thresholds and calculate_priority_score to justify the tier.",
            mcp_tools=("search_policy", "calculate_priority_score"),
        ),
        AgentSpec(
            "OfferPacketAgent",
            "Assembles the offer packet.",
            "Synthesize prior stages into an offer packet with a clear approve, refer, or decline decision and any conditions. Use list_playbook_steps for the loan-origination playbook and create_decision_log_entry to record the decision.",
            mcp_tools=("list_playbook_steps", "create_decision_log_entry"),
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
