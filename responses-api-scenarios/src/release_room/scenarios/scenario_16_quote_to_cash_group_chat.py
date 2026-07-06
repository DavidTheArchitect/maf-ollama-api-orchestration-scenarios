"""Scenario 16 quote-to-cash (Group Chat) for the Responses API sample.

Run directly with::

    python -m release_room.scenarios.scenario_16_quote_to_cash_group_chat
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

#: Group-chat-specific variants of the shared roles. The stage workers become
#: reviewers with a debate stance, and the quote owner closes each round-robin
#: cycle, ending the debate with an explicit readiness verdict.
_DEBATE_AGENTS = (
    replace(
        QUOTE_TRIGGER_AGENT,
        description="Argues from CRM readiness.",
        instructions=(
            "Argue whether the CRM conditions justify quoting now. Use crm_get_quote_trigger for the "
            "trigger facts and challenge the council if blockers exist. Do not invent CRM data."
        ),
    ),
    replace(
        CUSTOMER_CONTEXT_AGENT,
        description="Argues from the customer's context.",
        instructions=(
            "Argue whether the proposed quote fits this customer. Use crm_get_customer_profile and "
            "challenge SKU or terms choices that conflict with the account's segment, MSA status, or "
            "buying context."
        ),
    ),
    replace(
        SKU_DISCOVERY_AGENT,
        description="Proposes and defends the SKU selection.",
        instructions=(
            "Propose the SKU set that best fits the request. Use product_search_catalog, state list "
            "prices, and defend or revise your proposal when other reviewers challenge it."
        ),
    ),
    replace(
        PRODUCT_FIT_AGENT,
        description="Challenges SKU validity and compatibility.",
        instructions=(
            "Challenge the proposed SKUs. Use product_validate_skus (comma-separated SKU strings) and "
            "call out unknown, unavailable, or incompatible SKUs before the council converges."
        ),
    ),
    replace(
        PRICING_TERMS_AGENT,
        description="Challenges pricing and legal risk.",
        instructions=(
            "Challenge the pricing and terms. Use pricing_calculate_quote (comma-separated SKU strings) "
            "and legal_evaluate_terms, and flag discounts or clauses that need approvals."
        ),
    ),
    replace(
        QUOTE_GENERATION_AGENT,
        description="Synthesizes the debate and closes each round.",
        instructions=(
            "Synthesize the round: state the current SKU set, pricing, terms, and open challenges. "
            "Resolve gaps with your tools and quote_format_package when the package is ready. When the "
            "council has converged, end your turn with a line 'FINAL QUOTE RECOMMENDATION: <ready or "
            "not ready> - <one-sentence rationale>'."
        ),
    ),
)

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-group-chat",
    pattern="group-chat",
    title="Scenario 16: Quote-To-Cash (Group Chat)",
    learning_goal="Learn collaborative quote review where reviewers debate CRM readiness, customer fit, SKU selection, validity, and pricing risk, and the quote owner closes each round with a readiness verdict.",
    when_to_use="Use Group Chat when a visible debate and cross-check between roles improves the quote before it is finalized.",
    sample_input=SAMPLE_REQUEST,
    termination_phrases=("final quote recommendation",),
    agents=_DEBATE_AGENTS,
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
