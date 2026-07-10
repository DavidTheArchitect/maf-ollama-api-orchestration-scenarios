"""Magentic churn spike investigation job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-churn-spike-investigation",
    pattern="magentic",
    title="Magentic Churn Spike Investigation Job",
    learning_goal="Learn why an ambiguous root-cause hunt is the canonical magentic use case: three overlapping candidate causes mean no fixed pipeline fits, so a manager must plan, delegate to the right specialists, and replan as candidates are eliminated.",
    when_to_use="Use Invocations plus magentic orchestration for investigation jobs where which specialists matter — and in what order — only becomes clear as evidence arrives.",
    sample_task="Run an investigation job for the Q3 churn spike METRIC-CHURN-Q3 concentrated in SEGMENT-ENT-EU, identify the dominant driver, and return a remediation plan.",
    agents=(
        AgentSpec(
            "InvestigationManagerAgent",
            "Plans and delegates the investigation.",
            "Plan the churn investigation and delegate to specialists, replanning as candidate causes are confirmed or eliminated. Use list_playbook_steps for the churn-investigation playbook to structure the plan.",
            mcp_tools=("list_playbook_steps",),
        ),
        AgentSpec(
            "DataAnalystAgent",
            "Quantifies the anomaly.",
            "Quantify the churn anomaly against baseline and segment it. Use lookup_enterprise_record for the metric and segment records and calculate_priority_score to rank the severity.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "BillingOpsAgent",
            "Investigates the billing migration.",
            "Investigate whether the billing migration wave drove the churn. Use lookup_enterprise_record for the segment's migration timeline and search_policy for any related obligations.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "PricingAnalystAgent",
            "Investigates the pricing change.",
            "Investigate whether the September pricing change drove the churn. Use lookup_enterprise_record to compare the spike timing against the pricing change.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "ReliabilityAnalystAgent",
            "Investigates the regional outages.",
            "Investigate whether the P1 outages drove the churn. Use lookup_enterprise_record for the segment's outage history and its overlap with the spike window.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "RetentionPlannerAgent",
            "Drafts the remediation plan.",
            "Turn the confirmed driver into a remediation plan with an early-warning metric. Use create_decision_log_entry to record the plan and its owner.",
            mcp_tools=("create_decision_log_entry",),
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
