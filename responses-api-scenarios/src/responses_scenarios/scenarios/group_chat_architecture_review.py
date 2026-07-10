"""Group chat architecture review board scenario (MCP tools) for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-architecture-review",
    pattern="group-chat",
    title="Group Chat Architecture Review Board",
    learning_goal="Learn why a build-versus-buy decision is the canonical group chat use case: the tradeoffs live in different heads, each voice must react to the others' arguments in a visible transcript, and a chair owns the recorded decision.",
    when_to_use="Use Responses plus group chat orchestration when a decision request needs documented debate across engineering, security, finance, and delivery before a chair commits to an answer.",
    sample_input="Convene the architecture review board on ADR-2209 (customer notification service, build versus buy) and return a decision with conditions and an exit strategy.",
    termination_phrases=("decision:",),
    agents=(
        AgentSpec(
            "PlatformEngineerAgent",
            "Argues the build option's engineering reality.",
            "Argue the engineering cost and control tradeoffs of building in-house. Use lookup_enterprise_record for the decision record's build estimate and team utilization figures.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "SecurityArchitectAgent",
            "Argues security posture and data residency.",
            "Argue the security and data-residency implications of each option. Use lookup_enterprise_record for the vendor's data region and search_policy for the build-versus-buy review requirements.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "FinancePartnerAgent",
            "Argues total cost of ownership.",
            "Argue the total cost of ownership of each option over three years. Use search_policy for the review's cost coverage requirements and calculate_priority_score to rank the financial risk.",
            mcp_tools=("search_policy", "calculate_priority_score"),
        ),
        AgentSpec(
            "DeliveryLeadAgent",
            "Argues timeline and team capacity.",
            "Argue delivery risk: timeline, team capacity, and operational load. Use lookup_enterprise_record for the utilization and SLA figures in the decision record.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "ArchitectureChairAgent",
            "Records the board decision and closes each round.",
            "Weigh the debate. Use list_playbook_steps for the architecture-review playbook and create_decision_log_entry to record the outcome. When the board has heard engineering, security, finance, and delivery, end your turn with a line 'DECISION: build' or 'DECISION: buy' plus the conditions and the exit strategy.",
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
