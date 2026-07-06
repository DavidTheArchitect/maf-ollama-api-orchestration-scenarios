"""Magentic business continuity drill job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-business-continuity-drill",
    pattern="magentic",
    title="Magentic Business Continuity Drill Job",
    learning_goal="Learn how a magentic manager plans and delegates a continuity drill job, with specialists pulling facts from local MCP tools as the plan evolves.",
    when_to_use="Use Invocations plus magentic orchestration for open-ended job planning where a manager must dynamically delegate continuity-drill work across facilities, IT, communications, finance, and operations.",
    sample_task="Run a business continuity drill planning job for FACILITY-DC-EAST (overdue tier-1 site) across facilities, IT, communications, finance, and operations.",
    agents=(
        AgentSpec(
            "ContinuityManagerAgent",
            "Plans and delegates the drill.",
            "Plan the continuity drill and delegate to specialists, replanning as needed. Use list_playbook_steps for the continuity-drill playbook to structure the plan.",
            mcp_tools=("list_playbook_steps",),
        ),
        AgentSpec(
            "FacilitiesAgent",
            "Covers the physical facility.",
            "Plan the facility-side drill scope. Use lookup_enterprise_record to ground the facility's criticality and dependent services.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "ITRecoveryAgent",
            "Covers IT failover and recovery.",
            "Define IT failover and recovery objectives. Use search_policy for continuity rules and calculate_priority_score to rank recovery priorities.",
            mcp_tools=("search_policy", "calculate_priority_score"),
        ),
        AgentSpec(
            "CommunicationsAgent",
            "Covers stakeholder communications.",
            "Plan communications and stakeholder updates for the drill. Use search_policy to align with continuity requirements.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "FinanceAgent",
            "Covers financial contingencies.",
            "Plan financial contingencies for the drill. Use search_policy to relate the plan to continuity obligations.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "OperationsAgent",
            "Covers operational continuity and scheduling.",
            "Plan operational continuity and schedule the drill. Use lookup_enterprise_record for dependent services and create_decision_log_entry to record the drill plan.",
            mcp_tools=("lookup_enterprise_record", "create_decision_log_entry"),
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
