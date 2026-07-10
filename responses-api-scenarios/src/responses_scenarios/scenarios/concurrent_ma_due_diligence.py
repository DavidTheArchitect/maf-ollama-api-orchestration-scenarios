"""Concurrent M&A due diligence scenario (MCP tools) for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-ma-due-diligence",
    pattern="concurrent",
    title="Concurrent M&A Due Diligence",
    learning_goal="Learn why due diligence is the canonical concurrent use case: finance, legal, technology, and market workstreams are genuinely independent, deadline pressure rewards parallelism, and a deal lead must see every lane's findings before recommending.",
    when_to_use="Use Responses plus concurrent orchestration for deal requests where independent expert lanes can run at the same time and the recommendation is only as good as the slowest workstream you would otherwise wait on.",
    sample_input="Run due diligence on acquisition target TARGET-ACQ-STELLAR across finance, legal, technology, and market lanes and return a deal recommendation.",
    concurrent_synthesizer="DealLeadAgent",
    agents=(
        AgentSpec(
            "FinanceDiligenceAgent",
            "Assesses financial quality of the target.",
            "Assess revenue quality, growth, and customer concentration. Use lookup_enterprise_record for the target's financials and calculate_priority_score to rank the concentration risk.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "LegalDiligenceAgent",
            "Reviews litigation and legal exposure.",
            "Review litigation exposure and deal-blocking legal risk. Use lookup_enterprise_record for open litigation and search_policy for the due diligence gate rules on red flags.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "TechnologyDiligenceAgent",
            "Audits the technology and security posture.",
            "Audit the target's technology risk: certification status, deployment architecture, and integration cost. Use lookup_enterprise_record for the target's technical profile.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "MarketDiligenceAgent",
            "Evaluates market position and retention.",
            "Evaluate market position, churn, and competitive durability. Use lookup_enterprise_record for the target's retention figures and calculate_priority_score to rank market risk.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "DealLeadAgent",
            "Synthesizes the lanes into a recommendation.",
            "You receive all four diligence lanes. Apply the due diligence gate: any unmitigated red flag blocks a proceed recommendation. Use search_policy for the gate policy, list_playbook_steps for the due-diligence playbook, and create_decision_log_entry to record a proceed, renegotiate, or walk-away recommendation.",
            mcp_tools=("search_policy", "list_playbook_steps", "create_decision_log_entry"),
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
