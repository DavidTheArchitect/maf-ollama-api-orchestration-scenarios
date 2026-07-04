"""Concurrent security alert enrichment job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="concurrent-security-alert-enrichment",
    pattern="concurrent",
    title="Concurrent Security Alert Enrichment Job",
    learning_goal="Learn how a concurrent invocation lets independent specialists enrich the same alert in parallel with their own MCP facts, then hands every labelled finding to a summary agent that runs after fan-in.",
    when_to_use="Use Invocations plus concurrent orchestration for security jobs where several independent reviewers should enrich the same alert at once and a synthesis stage must combine what they found.",
    sample_task="Run an enrichment job for security alert ALERT-2298 across identity, endpoint, network, and data-loss dimensions.",
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
