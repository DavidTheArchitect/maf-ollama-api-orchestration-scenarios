"""Group chat policy exception board scenario (MCP tools) for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-policy-exception-board",
    pattern="group-chat",
    title="Group Chat Policy Exception Board",
    learning_goal="Learn how a group chat board debates a policy exception, with members grounding risk, business need, and compliance in local MCP tools before a chair records the recommendation.",
    when_to_use="Use Responses plus group chat orchestration when a visible debate among board members, backed by tool-grounded facts, should produce a documented exception decision.",
    sample_input="Convene the policy exception board on POLICY-EX-77 (temporary data residency waiver) and produce an approved recommendation with a compensating control and expiry.",
    agents=(
        AgentSpec(
            "RiskAssessorAgent",
            "Assesses the risk of the waiver.",
            "Argue the risk introduced by granting the exception. Use lookup_enterprise_record for the request and calculate_priority_score to rank the risk.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "BusinessNeedAgent",
            "Argues the business need.",
            "Argue the business need and urgency for the exception. Use search_policy to relate the need to existing policy.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "ComplianceReviewerAgent",
            "Checks compliance constraints.",
            "Identify compliance constraints and a required compensating control. Use search_policy to ground the policy exception board rules.",
            mcp_tools=("search_policy",),
        ),
        AgentSpec(
            "BoardChairAgent",
            "Records the board recommendation.",
            "Weigh the debate and state an 'approved' or 'denied' recommendation with a compensating control and expiry. Use list_playbook_steps for the policy-exception-board playbook and create_decision_log_entry to record it.",
            mcp_tools=("list_playbook_steps", "create_decision_log_entry"),
        ),
    ),
)
