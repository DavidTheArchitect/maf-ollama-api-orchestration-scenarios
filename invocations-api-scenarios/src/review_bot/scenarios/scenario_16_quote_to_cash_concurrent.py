"""Scenario 16 quote-to-cash (Concurrent) for the Invocations API sample.

Run directly with::

    python -m review_bot.scenarios.scenario_16_quote_to_cash_concurrent
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

#: Concurrent-specific variants of the shared roles. Each parallel lane is
#: self-sufficient: it pulls every fact it needs from its own tools so the
#: lanes are genuinely independent, and the quote owner runs after fan-in to
#: reconcile the labelled findings into one package.
_PRODUCT_FIT_PARALLEL = replace(
    PRODUCT_FIT_AGENT,
    instructions=(
        "Independently assess product fit from the request alone. Use product_search_catalog to find "
        "candidate SKUs for the requested capabilities, then product_validate_skus (comma-separated SKU "
        "strings) to flag unknown, unavailable, or incompatible SKUs before pricing."
    ),
    mcp_tools=("product_search_catalog", "product_validate_skus"),
)
_PRICING_TERMS_PARALLEL = replace(
    PRICING_TERMS_AGENT,
    instructions=(
        "Independently assess pricing and terms from the request alone. Use product_search_catalog to "
        "determine candidate SKUs, pricing_calculate_quote (comma-separated SKU strings) for totals, and "
        "legal_evaluate_terms for clauses and required approvals."
    ),
    mcp_tools=("product_search_catalog", "pricing_calculate_quote", "legal_evaluate_terms"),
)
_QUOTE_SYNTHESIZER = replace(
    QUOTE_GENERATION_AGENT,
    description="Reconciles the parallel findings into the final quote package.",
    instructions=(
        "You receive labelled findings from the trigger, customer, SKU, product-fit, and pricing lanes. "
        "Reconcile them (they may disagree on SKUs), resolve gaps with your tools, and assemble the final "
        "quote package with quote_format_package. Pass SKUs as comma-separated strings."
    ),
)

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-concurrent",
    pattern="concurrent",
    title="Scenario 16: Quote-To-Cash (Concurrent)",
    learning_goal="Learn how self-sufficient specialist lanes enrich the same quote request in parallel, and how the quote owner runs after fan-in to reconcile the labelled findings into one package.",
    when_to_use="Use Concurrent when enrichment lanes can each pull their own facts independently and a synthesis stage reconciles them before the deliverable.",
    sample_task=SAMPLE_REQUEST,
    concurrent_synthesizer=QUOTE_GENERATION_AGENT.name,
    agents=(
        QUOTE_TRIGGER_AGENT,
        CUSTOMER_CONTEXT_AGENT,
        SKU_DISCOVERY_AGENT,
        _PRODUCT_FIT_PARALLEL,
        _PRICING_TERMS_PARALLEL,
        _QUOTE_SYNTHESIZER,
    ),
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
