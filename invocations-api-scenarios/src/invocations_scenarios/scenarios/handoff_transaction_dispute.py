"""Handoff transaction dispute routing job scenario (MCP tools) for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="handoff-transaction-dispute",
    pattern="handoff",
    title="Handoff Transaction Dispute Job",
    learning_goal="Learn why dispute intake is the canonical handoff use case: the owning specialist genuinely depends on case facts, policy dictates the tie-break when signals conflict, and every outcome must end with one accountable customer communication.",
    when_to_use="Use Invocations plus handoff orchestration for dispute jobs where fraud, merchant-error, and subscription cases need different owners and a wrong route has real regulatory cost.",
    sample_task="Run a dispute routing job for transaction dispute DISPUTE-90455 (duplicate charge with a lost-card report) and return the resolution and customer communication.",
    handoff_finisher="DisputeCommsAgent",
    agents=(
        AgentSpec(
            "DisputeTriageAgent",
            "Classifies and routes the dispute.",
            "Decide which specialist should own the dispute: FraudReviewAgent, MerchantErrorAgent, "
            "or SubscriptionBillingAgent. Use lookup_enterprise_record for the dispute and "
            "search_policy for the routing rules. Per policy POL-DSP-04, any fraud indicator routes to "
            "FraudReviewAgent before provisional credit, even when a merchant-error signal is also present. "
            "End your reply with a line 'ROUTE: <AgentName>'.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
        ),
        AgentSpec(
            "FraudReviewAgent",
            "Investigates fraud indicators.",
            "Investigate the fraud indicators on the dispute before any credit decision. Use lookup_enterprise_record for the case facts and search_policy to ground the fraud-first routing rule.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
            route_keywords=("fraud", "lost", "stolen", "unauthorized"),
        ),
        AgentSpec(
            "MerchantErrorAgent",
            "Resolves merchant posting errors.",
            "Resolve duplicate postings and merchant billing errors. Use lookup_enterprise_record for the posting facts and search_policy for the provisional credit timeline.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
            route_keywords=("duplicate", "merchant", "posting", "error"),
        ),
        AgentSpec(
            "SubscriptionBillingAgent",
            "Handles post-cancellation subscription charges.",
            "Resolve recurring charges billed after cancellation. Use lookup_enterprise_record to confirm the cancellation and search_policy for the merchant-error credit rules.",
            mcp_tools=("lookup_enterprise_record", "search_policy"),
            route_keywords=("subscription", "recurring", "cancellation", "cancelled"),
        ),
        AgentSpec(
            "DisputeCommsAgent",
            "Drafts the customer communication.",
            "You receive the routed specialist's resolution. Draft a clear, empathetic customer message covering the decision, the provisional credit status, and the regulatory clock. Use create_decision_log_entry to record the communicated outcome.",
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
