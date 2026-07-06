"""Concurrent security alert enrichment scenario (MCP tools) for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-security-alert-enrichment",
    pattern="concurrent",
    title="Concurrent Security Alert Enrichment",
    learning_goal="Learn how concurrent orchestration lets independent specialists enrich the same alert in parallel with their own MCP facts, then hands every labelled finding to a summary agent that runs after fan-in.",
    when_to_use="Use Responses plus concurrent orchestration when several independent reviewers should enrich the same security alert at once and a synthesis stage must combine what they found.",
    sample_input="Enrich security alert ALERT-2298 (anomalous OAuth token usage) across identity, endpoint, network, and data-loss dimensions, then summarize.",
    concurrent_synthesizer="IncidentSummaryAgent",
    agents=(
        AgentSpec(
            "IdentityEnrichmentAgent",
            "Enriches the identity dimension.",
            "Analyze affected accounts, tokens, and sessions. Use lookup_enterprise_record for the alert and search_policy for identity response rules.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "EndpointEnrichmentAgent",
            "Enriches the endpoint dimension.",
            "Analyze affected devices and processes. Use lookup_enterprise_record to ground the affected endpoint count.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "NetworkEnrichmentAgent",
            "Enriches the network dimension.",
            "Analyze source ASNs and destinations. Use lookup_enterprise_record to confirm the alert's network indicators.",
            mcp_tools=("lookup_enterprise_record",),
        ),
        AgentSpec(
            "DataLossEnrichmentAgent",
            "Assesses data-loss exposure.",
            "Evaluate data-loss indicators and exposure. Use lookup_enterprise_record and calculate_priority_score to rank the exposure.",
            mcp_tools=("lookup_enterprise_record", "calculate_priority_score"),
        ),
        AgentSpec(
            "IncidentSummaryAgent",
            "Summarizes the enriched alert after fan-in.",
            "You receive the labelled findings from the identity, endpoint, network, and data-loss enrichment agents. Combine them into one incident summary. Use list_playbook_steps for the security-enrichment playbook and create_decision_log_entry to record the triage decision.",
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
