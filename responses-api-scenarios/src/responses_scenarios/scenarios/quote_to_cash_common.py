"""Shared building blocks for the Scenario 16 quote-to-cash family.

All five pattern variants reuse the same six agent roles and the same business
story so learners can compare orchestration patterns directly. The agents are
grounded by the local ``quote_to_cash_context`` MCP server.
"""

from __future__ import annotations

from ..agents import AgentSpec

MCP_SERVER = "quote_to_cash_context"

#: One shared quote request used as the sample input/task across all variants.
SAMPLE_REQUEST = (
    "Create a quote for opportunity OPP-5001 (account ACC-3300, Contoso Manufacturing). "
    "They want the analytics platform with edge connectors and premier support, with standard "
    "enterprise terms, and they are targeting a 25 percent discount -- check what approvals "
    "that requires."
)


def _agent(
    name: str,
    description: str,
    instructions: str,
    tools: tuple[str, ...],
) -> AgentSpec:
    return AgentSpec(
        name,
        description,
        instructions,
        mcp_tools=tools,
        mcp_server=MCP_SERVER,
    )


QUOTE_TRIGGER_AGENT = _agent(
    "QuoteTriggerAgent",
    "Monitors CRM for quote-trigger conditions.",
    "Check whether the CRM conditions to create a quote exist. Use crm_get_quote_trigger to report "
    "quote-readiness, which trigger conditions are met, and any blockers. Do not invent CRM data.",
    ("crm_get_quote_trigger",),
)
CUSTOMER_CONTEXT_AGENT = _agent(
    "CustomerContextAgent",
    "Enriches the customer profile from CRM.",
    "Enrich the customer profile. Use crm_get_customer_profile to capture customer name, address, MSA "
    "status, account status, segment, and buying context for the quote.",
    ("crm_get_customer_profile",),
)
SKU_DISCOVERY_AGENT = _agent(
    "SkuDiscoveryAgent",
    "Finds SKUs, bundles, and catalog entries.",
    "Identify candidate SKUs, bundles, and catalog entries that fit the customer's need. Use "
    "product_search_catalog and list the matching SKUs with names and list prices.",
    ("product_search_catalog",),
)
PRODUCT_FIT_AGENT = _agent(
    "ProductFitAgent",
    "Validates product compatibility and availability.",
    "Validate product compatibility, availability, and SKU completeness. Use product_validate_skus with "
    "comma-separated SKU strings, and flag any unknown, unavailable, or incompatible SKUs before pricing.",
    ("product_validate_skus",),
)
PRICING_TERMS_AGENT = _agent(
    "PricingTermsAgent",
    "Resolves pricing, finance, and legal terms.",
    "Resolve pricing, discount, finance, and legal constraints. Use pricing_calculate_quote with "
    "comma-separated SKU strings for totals and legal_evaluate_terms for clauses and required approvals.",
    ("pricing_calculate_quote", "legal_evaluate_terms"),
)
QUOTE_GENERATION_AGENT = _agent(
    "QuoteGenerationAgent",
    "Generates the final customer-ready quote package.",
    "Assemble the final quote package with pricing, SKUs, legal/T&C notes, and a customer-ready format. "
    "If context is missing, call the quote trigger, customer profile, catalog, SKU validation, pricing, "
    "and legal tools before quote_format_package. Pass SKUs as comma-separated strings.",
    (
        "crm_get_quote_trigger",
        "crm_get_customer_profile",
        "product_search_catalog",
        "product_validate_skus",
        "pricing_calculate_quote",
        "legal_evaluate_terms",
        "quote_format_package",
    ),
)

#: The six roles in their natural quote-to-cash staging order.
STAGED_AGENTS: tuple[AgentSpec, ...] = (
    QUOTE_TRIGGER_AGENT,
    CUSTOMER_CONTEXT_AGENT,
    SKU_DISCOVERY_AGENT,
    PRODUCT_FIT_AGENT,
    PRICING_TERMS_AGENT,
    QUOTE_GENERATION_AGENT,
)


def staged_agents() -> tuple[AgentSpec, ...]:
    """Agents in staging order (trigger -> customer -> product -> pricing -> quote)."""

    return STAGED_AGENTS


def manager_first_agents() -> tuple[AgentSpec, ...]:
    """Agents with the quote owner first, for Magentic (manager + specialists)."""

    return (
        QUOTE_GENERATION_AGENT,
        QUOTE_TRIGGER_AGENT,
        CUSTOMER_CONTEXT_AGENT,
        SKU_DISCOVERY_AGENT,
        PRODUCT_FIT_AGENT,
        PRICING_TERMS_AGENT,
    )
