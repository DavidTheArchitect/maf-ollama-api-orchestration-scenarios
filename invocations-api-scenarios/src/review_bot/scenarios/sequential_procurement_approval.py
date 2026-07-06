"""Sequential procurement approval job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-procurement-approval",
    pattern="sequential",
    title="Sequential Procurement Approval Job",
    learning_goal="Learn how a structured invocation can drive a fixed approval pipeline whose stages call local MCP tools for enterprise records, policies, and playbooks.",
    when_to_use="Use Invocations plus sequential orchestration for procurement jobs that must walk through fixed intake, budget, security, legal, and packaging stages with tool-grounded facts.",
    sample_task="Run a procurement approval job for vendor VENDOR-4471 (Northwind Analytics) and return an approval packet.",
    agents=(
        AgentSpec(
            "IntakeAgent",
            "Normalizes the procurement job.",
            "Turn the job into a concrete work order. Use lookup_enterprise_record to pull the vendor record and restate scope, cost, and owner.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "BudgetAgent",
            "Checks spend authority.",
            "Validate the spend against authorization thresholds. Use search_policy for spend rules and calculate_priority_score to rank budget risk.",
            mcp_tools=("search_policy", "calculate_priority_score"),
        ),
        AgentSpec(
            "SecurityAgent",
            "Checks vendor security posture.",
            "Assess vendor security review status. Use lookup_enterprise_record and search_policy to confirm whether the security review meets policy.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "LegalAgent",
            "Captures contract and data terms.",
            "Identify legal and data-protection terms that must appear in the contract. Use search_policy to ground residency and data-handling requirements.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "ApprovalPacketAgent",
            "Assembles the approval packet.",
            "Synthesize prior stages into an approval packet with a go/no-go recommendation. Use list_playbook_steps for the procurement-approval playbook and create_decision_log_entry to record the decision.",
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
