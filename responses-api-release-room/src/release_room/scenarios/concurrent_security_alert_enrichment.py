"""Concurrent security alert enrichment scenario (MCP tools) for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-security-alert-enrichment",
    pattern="concurrent",
    title="Concurrent Security Alert Enrichment",
    learning_goal="Learn how concurrent orchestration lets independent specialists enrich the same alert in parallel, each pulling its own facts from local MCP tools.",
    when_to_use="Use Responses plus concurrent orchestration when several independent reviewers should enrich the same security alert at once before a summary is assembled.",
    sample_input="Enrich security alert ALERT-2298 (anomalous OAuth token usage) across identity, endpoint, network, and data-loss dimensions, then summarize.",
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
            "Summarizes the enriched alert.",
            "Combine the independent perspectives into one incident summary. Use list_playbook_steps for the security-enrichment playbook and create_decision_log_entry to record the triage decision.",
            mcp_tools=("list_playbook_steps", "create_decision_log_entry"),
        ),
    ),
)
