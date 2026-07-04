"""Scenario 16 quote-to-cash (Handoff) for the Responses API sample.

Run directly with::

    python -m release_room.scenarios.scenario_16_quote_to_cash_handoff
"""

from __future__ import annotations

from dataclasses import replace

from .quote_to_cash_common import (
    CUSTOMER_CONTEXT_AGENT,
    PRICING_TERMS_AGENT,
    PRODUCT_FIT_AGENT,
    QUOTE_GENERATION_AGENT,
    QUOTE_TRIGGER_AGENT,
    SAMPLE_REQUEST,
    SKU_DISCOVERY_AGENT,
)
from .types import ScenarioSpec

#: Handoff-specific variants of the shared roles: the trigger agent gains a
#: routing charter, the specialists gain curated route keywords, and the quote
#: owner always finishes the package after the routed specialist reports.
_ROUTING_TRIGGER_AGENT = replace(
    QUOTE_TRIGGER_AGENT,
    description="Checks quote readiness and routes the biggest gap.",
    instructions=(
        "Check whether the CRM conditions to create a quote exist. Use crm_get_quote_trigger to report "
        "quote-readiness, trigger conditions, and blockers. Do not invent CRM data. Then pick the "
        "specialist whose input the quote needs most: CustomerContextAgent, SkuDiscoveryAgent, "
        "ProductFitAgent, or PricingTermsAgent. End your reply with a line 'ROUTE: <AgentName>'."
    ),
)

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-handoff",
    pattern="handoff",
    title="Scenario 16: Quote-To-Cash (Handoff)",
    learning_goal="Learn dynamic routing where the trigger agent names the specialist the quote needs most (validated by a code-defined router), and the quote-generation owner always finishes the package.",
    when_to_use="Use Handoff when the next specialist depends on context, the model should choose the route within an allowed handoff graph, and a fixed owner must complete the deliverable.",
    sample_input=SAMPLE_REQUEST,
    handoff_finisher=QUOTE_GENERATION_AGENT.name,
    agents=(
        _ROUTING_TRIGGER_AGENT,
        replace(CUSTOMER_CONTEXT_AGENT, route_keywords=("profile", "account", "msa", "segment")),
        replace(SKU_DISCOVERY_AGENT, route_keywords=("sku", "catalog", "bundle", "search")),
        replace(PRODUCT_FIT_AGENT, route_keywords=("validate", "compatibility", "availability", "fit")),
        replace(PRICING_TERMS_AGENT, route_keywords=("pricing", "discount", "legal", "terms")),
        QUOTE_GENERATION_AGENT,
    ),
)


async def run_sample(**config_overrides) -> str:
    """Build and run this scenario in-process, returning readable output text."""

    from ..workflows import run_scenario_sample

    return await run_scenario_sample(SCENARIO.id, **config_overrides)


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(run_sample()))
