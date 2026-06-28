"""Local, deterministic ``quote-to-cash-context`` MCP server.

This is a self-contained `FastMCP <https://github.com/modelcontextprotocol>`_
stdio server that simulates the enterprise systems behind a quote-to-cash flow
(CRM, product/SKU catalog, pricing/finance, and legal). It is intentionally
safe so the Scenario 16 quote-to-cash orchestrations can run anywhere:

* No network calls, no credentials, no environment lookups.
* No writes; tools only return embedded fixture data.
* Every call is deterministic, so tests and notebooks are reproducible.

Run it directly with::

    python -m review_bot.mcp_servers.quote_to_cash_context

Agents attach to it through ``agent_framework.MCPStdioTool`` using
``sys.executable -m review_bot.mcp_servers.quote_to_cash_context``.
"""

from __future__ import annotations

import hashlib
from typing import Any

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "quote-to-cash-context"

mcp = FastMCP(SERVER_NAME)

# ---------------------------------------------------------------------------
# Embedded fixtures (no external sources).
# ---------------------------------------------------------------------------

_QUOTE_TRIGGERS: dict[str, dict[str, Any]] = {
    "OPP-5001": {
        "opportunity_id": "OPP-5001",
        "account_id": "ACC-3300",
        "stage": "Negotiation",
        "quote_ready": True,
        "trigger_conditions": [
            "Opportunity stage is Negotiation or later.",
            "Primary contact and billing account are set.",
            "Budget is confirmed by the customer.",
        ],
        "blocking_conditions": [],
    },
    "OPP-5002": {
        "opportunity_id": "OPP-5002",
        "account_id": "ACC-3301",
        "stage": "Discovery",
        "quote_ready": False,
        "trigger_conditions": [
            "Opportunity stage is Negotiation or later.",
        ],
        "blocking_conditions": [
            "Opportunity is still in Discovery.",
            "No confirmed budget on the opportunity.",
        ],
    },
}

_CUSTOMER_PROFILES: dict[str, dict[str, Any]] = {
    "ACC-3300": {
        "account_id": "ACC-3300",
        "customer_name": "Contoso Manufacturing",
        "address": "120 Industrial Way, Aurora, IL 60502, USA",
        "msa_status": "signed",
        "account_status": "active",
        "segment": "enterprise",
        "buying_context": "Expanding plant automation; standardizing on one analytics platform.",
    },
    "ACC-3301": {
        "account_id": "ACC-3301",
        "customer_name": "Fabrikam Logistics",
        "address": "44 Harbor Rd, Tacoma, WA 98402, USA",
        "msa_status": "in_review",
        "account_status": "active",
        "segment": "mid-market",
        "buying_context": "Evaluating route-optimization add-ons for peak season.",
    },
}

_CATALOG: tuple[dict[str, Any], ...] = (
    {"sku": "SKU-ANALYTICS-CORE", "name": "Analytics Core Platform", "bundle": "platform", "list_price": 48000, "keywords": ("analytics", "platform", "core")},
    {"sku": "SKU-ANALYTICS-EDGE", "name": "Edge Connector Pack", "bundle": "platform", "list_price": 12000, "keywords": ("analytics", "edge", "connector", "automation")},
    {"sku": "SKU-SUPPORT-PREM", "name": "Premier Support (12 mo)", "bundle": "support", "list_price": 9000, "keywords": ("support", "premier", "service")},
    {"sku": "SKU-ROUTE-OPT", "name": "Route Optimization Add-on", "bundle": "logistics", "list_price": 15000, "keywords": ("route", "optimization", "logistics")},
    {"sku": "SKU-TRAINING-1", "name": "Onboarding & Training", "bundle": "services", "list_price": 6000, "keywords": ("training", "onboarding", "services")},
)

_SKU_INDEX = {entry["sku"]: entry for entry in _CATALOG}

# SKUs that are not compatible together (for product validation).
_INCOMPATIBLE_PAIRS = {("SKU-ROUTE-OPT", "SKU-ANALYTICS-EDGE")}
# SKUs that are out of stock / unavailable.
_UNAVAILABLE_SKUS = {"SKU-TRAINING-1"}

_LEGAL_TERMS: dict[str, dict[str, Any]] = {
    "enterprise": {
        "segment": "enterprise",
        "risk_level": "medium",
        "clauses": [
            "Net-45 payment terms.",
            "Standard MSA governs; no bespoke indemnity without legal review.",
            "Auto-renewal with 60-day opt-out.",
        ],
        "approvals_required": ["Deal desk", "Legal (if discount > 20%)"],
    },
    "mid-market": {
        "segment": "mid-market",
        "risk_level": "low",
        "clauses": [
            "Net-30 payment terms.",
            "Click-through terms acceptable below $50k.",
        ],
        "approvals_required": ["Deal desk"],
    },
}


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        pieces = value.replace(";", ",").replace("\n", ",").split(",")
        return [piece.strip() for piece in pieces if piece.strip()]
    try:
        items = iter(value)
    except TypeError:
        text = str(value).strip()
        return [text] if text else []
    flattened: list[str] = []
    for item in items:
        flattened.extend(_string_list(item))
    return flattened


# ---------------------------------------------------------------------------
# Tools.
# ---------------------------------------------------------------------------


@mcp.tool()
def crm_get_quote_trigger(opportunity_id: str = "OPP-5001") -> dict[str, Any]:
    """Return CRM trigger state for an opportunity.

    Tells the trigger agent whether the CRM conditions to create a quote are
    satisfied. Unknown opportunities return ``found: false``.
    """

    key = (opportunity_id or "").strip().upper()
    record = _QUOTE_TRIGGERS.get(key)
    if record is None:
        return {"found": False, "opportunity_id": opportunity_id, "known_ids": sorted(_QUOTE_TRIGGERS)}
    return {"found": True, **record}


@mcp.tool()
def crm_get_customer_profile(account_id: str = "ACC-3300") -> dict[str, Any]:
    """Return the enriched CRM customer profile for an account."""

    key = (account_id or "").strip().upper()
    record = _CUSTOMER_PROFILES.get(key)
    if record is None:
        return {"found": False, "account_id": account_id, "known_ids": sorted(_CUSTOMER_PROFILES)}
    return {"found": True, **record}


@mcp.tool()
def product_search_catalog(query: str = "analytics platform") -> dict[str, Any]:
    """Search the product/SKU catalog with a simple keyword match.

    Returns matching SKUs, names, bundles, and list prices. With an empty query
    it returns the full catalog so the discovery agent always has data.
    """

    terms = [term for term in (query or "").lower().replace(",", " ").split() if term]
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in _CATALOG:
        haystack = " ".join((entry["name"], entry["bundle"], " ".join(entry["keywords"]))).lower()
        score = sum(1 for term in terms if term in haystack)
        if score or not terms:
            scored.append((score, entry))
    scored.sort(key=lambda item: (-item[0], item[1]["sku"]))
    matches = [
        {"sku": e["sku"], "name": e["name"], "bundle": e["bundle"], "list_price": e["list_price"], "match_score": s}
        for s, e in scored
    ]
    return {"query": query, "match_count": len(matches), "matches": matches}


@mcp.tool()
def product_validate_skus(skus: str = "") -> dict[str, Any]:
    """Validate SKU compatibility, availability, and completeness.

    Returns a per-SKU validation plus an overall ``all_valid`` flag. Unknown
    SKUs are reported as incomplete.
    """

    requested = _string_list(skus) or [entry["sku"] for entry in _CATALOG[:2]]
    requested_set = {sku.strip().upper() for sku in requested}
    validated: list[dict[str, Any]] = []
    for sku in requested:
        key = sku.strip().upper()
        known = key in _SKU_INDEX
        available = known and key not in _UNAVAILABLE_SKUS
        compatible = not any(
            {key, other} == set(pair) for pair in _INCOMPATIBLE_PAIRS for other in requested_set
        )
        validated.append(
            {
                "sku": key,
                "known": known,
                "compatible": compatible,
                "available": available,
                "complete": bool(known and available and compatible),
            }
        )
    all_valid = bool(validated) and all(item["complete"] for item in validated)
    return {"requested": requested, "validated": validated, "all_valid": all_valid}


@mcp.tool()
def pricing_calculate_quote(skus: str = "", discount_pct: float = 0.0) -> dict[str, Any]:
    """Calculate quote pricing for a set of SKUs.

    Sums list prices for known SKUs, applies a clamped discount (0-40%), and
    returns deterministic line items and totals.
    """

    requested = _string_list(skus) or [entry["sku"] for entry in _CATALOG[:2]]
    line_items: list[dict[str, Any]] = []
    subtotal = 0
    for sku in requested:
        key = sku.strip().upper()
        entry = _SKU_INDEX.get(key)
        price = int(entry["list_price"]) if entry else 0
        subtotal += price
        line_items.append({"sku": key, "list_price": price, "in_catalog": entry is not None})
    try:
        pct = float(discount_pct)
    except (TypeError, ValueError):
        pct = 0.0
    pct = max(0.0, min(40.0, pct))
    discount = round(subtotal * pct / 100.0, 2)
    total = round(subtotal - discount, 2)
    return {
        "currency": "USD",
        "line_items": line_items,
        "subtotal": subtotal,
        "discount_pct": pct,
        "discount": discount,
        "total": total,
    }


@mcp.tool()
def legal_evaluate_terms(segment: str = "enterprise", discount_pct: float = 0.0) -> dict[str, Any]:
    """Return legal/contract terms and required approvals for a segment."""

    key = (segment or "").strip().lower()
    terms = _LEGAL_TERMS.get(key, _LEGAL_TERMS["enterprise"])
    try:
        pct = float(discount_pct)
    except (TypeError, ValueError):
        pct = 0.0
    approvals = list(terms["approvals_required"])
    if pct > 20 and "Legal review" not in approvals:
        approvals.append("Legal review (discount over 20%)")
    return {
        "segment": terms["segment"],
        "risk_level": terms["risk_level"],
        "clauses": list(terms["clauses"]),
        "approvals_required": approvals,
    }


@mcp.tool()
def quote_format_package(
    customer_name: str = "Contoso Manufacturing",
    total: float = 0.0,
    skus: str = "",
) -> dict[str, Any]:
    """Format the final customer-ready quote package.

    Returns a deterministic quote id and the standard sections. Performs no
    writes; it only describes the package that would be sent.
    """

    requested = _string_list(skus)
    fingerprint = "|".join([customer_name, ",".join(requested), f"{float(total or 0.0):.2f}"])
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:8]
    return {
        "quote_id": f"Q2C-{digest}",
        "format": "pdf",
        "customer_name": customer_name,
        "total": round(float(total or 0.0), 2),
        "skus": [sku.strip().upper() for sku in requested],
        "sections": ["Cover", "Customer & MSA", "Line Items & Pricing", "Terms & Conditions", "Signature"],
        "customer_ready": True,
    }


def list_tool_names() -> tuple[str, ...]:
    """Return the names of every tool registered on this server."""

    return tuple(sorted(tool.name for tool in mcp._tool_manager.list_tools()))


AVAILABLE_TOOLS: tuple[str, ...] = list_tool_names()


def main() -> None:
    """Run the server over stdio."""

    mcp.run("stdio")


if __name__ == "__main__":
    main()
