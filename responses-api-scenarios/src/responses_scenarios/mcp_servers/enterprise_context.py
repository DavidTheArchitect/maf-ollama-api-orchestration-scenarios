"""Local, deterministic ``enterprise-context`` MCP server.

This module is a self-contained `FastMCP <https://github.com/modelcontextprotocol>`_
stdio server. It is intentionally boring and safe so the Microsoft Agent
Framework MCP scenarios can run anywhere:

* No network calls, no credentials, no environment lookups.
* No writes to disk or anywhere else; ``create_decision_log_entry`` only returns
  the entry it *would* have written, with a deterministic id.
* All data is embedded sample enterprise data, so every call is reproducible.

Run it directly with::

    python -m responses_scenarios.mcp_servers.enterprise_context

Agents attach to it through ``agent_framework.MCPStdioTool`` using
``sys.executable -m responses_scenarios.mcp_servers.enterprise_context``.
"""

from __future__ import annotations

import hashlib
from typing import Any

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "enterprise-context"

mcp = FastMCP(SERVER_NAME)

# ---------------------------------------------------------------------------
# Embedded sample enterprise data (no external sources).
# ---------------------------------------------------------------------------

_ENTERPRISE_RECORDS: dict[str, dict[str, Any]] = {
    "VENDOR-4471": {
        "type": "vendor",
        "name": "Northwind Analytics",
        "category": "data-platform",
        "annual_cost_usd": 184000,
        "data_classification": "confidential",
        "security_review": "expired",
        "owner": "Procurement",
        "notes": "Requested for the billing analytics rollout; SOC 2 report is 14 months old.",
    },
    "ALERT-2298": {
        "type": "security_alert",
        "name": "Anomalous OAuth token usage",
        "severity": "high",
        "affected_users": 3,
        "affected_endpoints": 2,
        "data_loss_indicators": False,
        "token_rotation_completed": False,
        "owner": "SecOps",
        "notes": "Three service accounts issued tokens from an unrecognized ASN within 9 minutes.",
    },
    "CLAIM-88120": {
        "type": "claim",
        "name": "Water damage exception",
        "amount_usd": 42150,
        "policy_id": "POLICY-PROP-12",
        "fraud_signals": 1,
        "compliance_holds": 0,
        "owner": "Claims",
        "notes": "Exceeds auto-approval threshold and includes one mismatched invoice date.",
    },
    "CLAIM-88121": {
        "type": "claim",
        "name": "Storm damage exception",
        "amount_usd": 58900,
        "policy_id": "POLICY-PROP-12",
        "fraud_signals": 2,
        "compliance_holds": 1,
        "owner": "Claims",
        "notes": "Duplicate invoice numbers plus an active regulatory hold; per POL-CLM-09 the fraud review precedes any payment decision.",
    },
    "POLICY-EX-77": {
        "type": "policy_exception",
        "name": "Temporary data residency waiver",
        "requested_by": "EU Sales",
        "risk_area": "data-residency",
        "duration_days": 90,
        "owner": "Governance",
        "notes": "Requests storing EU lead data in us-east during a vendor migration window.",
    },
    "FACILITY-DC-EAST": {
        "type": "facility",
        "name": "East Regional Data Center",
        "criticality": "tier-1",
        "dependent_services": ["billing", "auth", "exports"],
        "last_drill_days_ago": 410,
        "owner": "Operations",
        "notes": "Primary site for billing and auth; continuity drill is overdue.",
    },
    "FACILITY-DC-WEST": {
        "type": "facility",
        "name": "West Regional Data Center",
        "criticality": "tier-2",
        "dependent_services": ["reporting", "archive"],
        "last_drill_days_ago": 120,
        "owner": "Operations",
        "notes": "Secondary site with a current drill; a contrast case when prioritizing scope.",
    },
    "LOAN-73021": {
        "type": "loan_application",
        "name": "Home purchase mortgage application",
        "amount_usd": 384000,
        "credit_score": 764,
        "dti_ratio": 0.31,
        "ltv_ratio": 0.80,
        "employment_years": 6,
        "owner": "Lending",
        "notes": "Salaried applicant with two years of W-2s on file; a clean pass through every underwriting stage.",
    },
    "LOAN-73022": {
        "type": "loan_application",
        "name": "Home purchase mortgage application (marginal)",
        "amount_usd": 402000,
        "credit_score": 668,
        "dti_ratio": 0.44,
        "ltv_ratio": 0.92,
        "employment_years": 1,
        "owner": "Lending",
        "notes": "Self-employed applicant; DTI and LTV both exceed the POL-LEND-01 referral limits, so manual underwriting and compensating factors are required.",
    },
    "TARGET-ACQ-STELLAR": {
        "type": "acquisition_target",
        "name": "Stellar Metrics Ltd",
        "sector": "SaaS product analytics",
        "arr_usd": 24000000,
        "arr_growth_pct": 38,
        "logo_churn_pct": 9,
        "top_customer_revenue_share": 0.34,
        "open_litigation": 1,
        "soc2_status": "none",
        "owner": "Corporate Development",
        "notes": "Fast grower with one pending patent dispute, no SOC 2, a single-region deployment, and a third of revenue from one customer.",
    },
    "TARGET-ACQ-HARBOR": {
        "type": "acquisition_target",
        "name": "Harbor Data GmbH",
        "sector": "EU data-residency analytics",
        "arr_usd": 11000000,
        "arr_growth_pct": 12,
        "logo_churn_pct": 4,
        "top_customer_revenue_share": 0.11,
        "open_litigation": 0,
        "soc2_status": "current",
        "owner": "Corporate Development",
        "notes": "Slower but clean: current certifications, diversified revenue, and an EU footprint; the contrast case for the diligence lanes.",
    },
    "DISPUTE-90455": {
        "type": "transaction_dispute",
        "name": "Duplicate charge with lost-card report",
        "amount_usd": 1249.99,
        "merchant": "TechnoMart Online",
        "duplicate_posting": True,
        "card_reported_lost": True,
        "cardholder_present": False,
        "days_since_posting": 3,
        "owner": "Card Services",
        "notes": "The same amount posted twice (a merchant-error signal) and the cardholder reported the card lost the same week (a fraud signal); POL-DSP-04 makes fraud review win that tie.",
    },
    "DISPUTE-90456": {
        "type": "transaction_dispute",
        "name": "Subscription billed after cancellation",
        "amount_usd": 29.99,
        "merchant": "StreamBox Media",
        "duplicate_posting": False,
        "card_reported_lost": False,
        "cancellation_confirmed": True,
        "days_since_posting": 12,
        "owner": "Card Services",
        "notes": "A recurring charge posted twelve days after a confirmed cancellation; a clean subscription dispute with no fraud signal.",
    },
    "ADR-2209": {
        "type": "architecture_decision",
        "name": "Customer notification service: build versus buy",
        "annual_buy_cost_usd": 96000,
        "build_estimate_eng_quarters": 2,
        "vendor_sla_pct": 99.9,
        "vendor_data_region": "us-only",
        "platform_team_utilization_pct": 85,
        "owner": "Architecture",
        "notes": "The vendor processes data in the US only while a quarter of customers are in the EU; the build option lands on a platform team already at 85% utilization.",
    },
    "METRIC-CHURN-Q3": {
        "type": "metric_anomaly",
        "name": "Q3 enterprise churn spike",
        "baseline_monthly_churn_pct": 1.8,
        "current_monthly_churn_pct": 4.1,
        "spike_start": "week of Sep 8",
        "support_ticket_trend": "flat",
        "nps_delta": -12,
        "owner": "Customer Success",
        "notes": "Churn more than doubled while support volume stayed flat; the spike overlaps a Sep 1 pricing change and billing migration wave 2, so the cause is genuinely ambiguous.",
    },
    "SEGMENT-ENT-EU": {
        "type": "customer_segment",
        "name": "Enterprise EU segment",
        "account_count": 214,
        "arr_usd": 18600000,
        "renewal_concentration": "Q4-heavy",
        "recent_events": [
            "billing migration wave 2 (Sep 5-12)",
            "new DPA requirement emails",
            "P1 outages on Aug 28 and Sep 9",
        ],
        "owner": "Customer Success",
        "notes": "The segment where the churn spike concentrates; three overlapping candidate causes give an investigation real material to eliminate.",
    },
}

_POLICY_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "POL-PROC-01",
        "title": "Vendor Security Review",
        "summary": "Vendors handling confidential data require a security review no older than 12 months before purchase.",
        "keywords": ("vendor", "security", "procurement", "soc2", "review", "purchase"),
    },
    {
        "id": "POL-PROC-02",
        "title": "Spend Authorization Thresholds",
        "summary": "Spend above 100k USD requires budget owner plus finance director approval.",
        "keywords": ("budget", "spend", "procurement", "approval", "finance", "threshold"),
    },
    {
        "id": "POL-PROC-03",
        "title": "Regional Processing Exception",
        "summary": "Vendors may process confidential data in-region for up to 30 days during a migration window with security sign-off, even while the annual review is pending.",
        "keywords": ("vendor", "regional", "migration", "exception", "security", "processing"),
    },
    {
        "id": "POL-SEC-04",
        "title": "Identity Compromise Response",
        "summary": "Suspected token or identity compromise requires credential rotation and session revocation within one hour.",
        "keywords": ("identity", "token", "oauth", "security", "incident", "rotation"),
    },
    {
        "id": "POL-CLM-09",
        "title": "Claim Exception Routing",
        "summary": "Claims above the auto-approval threshold or with any fraud signal route to a specialist before payment.",
        "keywords": ("claim", "exception", "fraud", "payment", "threshold"),
    },
    {
        "id": "POL-GOV-03",
        "title": "Policy Exception Board",
        "summary": "Risk waivers require a documented business need, a compensating control, and a fixed expiry. Maximum waiver duration is 60 days.",
        "keywords": ("policy", "exception", "waiver", "risk", "compliance", "governance", "residency"),
    },
    {
        "id": "POL-BCP-02",
        "title": "Business Continuity Drills",
        "summary": "Tier-1 facilities must complete a continuity drill at least every 365 days.",
        "keywords": ("continuity", "drill", "facility", "tier-1", "operations", "recovery"),
    },
    {
        "id": "POL-LEND-01",
        "title": "Manual Underwriting Referral",
        "summary": "Loan applications with a debt-to-income ratio above 0.43 or a loan-to-value ratio above 0.90 require senior underwriter review and documented compensating factors before pricing.",
        "keywords": ("loan", "underwriting", "dti", "ltv", "credit", "referral", "lending"),
    },
    {
        "id": "POL-MA-02",
        "title": "Due Diligence Gate",
        "summary": "Acquisition recommendations require findings from the finance, legal, technology, and market workstreams; any single red flag blocks a proceed recommendation until a documented mitigation exists.",
        "keywords": ("acquisition", "diligence", "merger", "workstream", "target", "gate"),
    },
    {
        "id": "POL-DSP-04",
        "title": "Dispute Routing and Provisional Credit",
        "summary": "Disputes with any fraud indicator route to fraud review before provisional credit; pure merchant errors receive provisional credit within two business days; every dispute is acknowledged within ten business days.",
        "keywords": ("dispute", "fraud", "chargeback", "credit", "merchant", "routing", "card"),
    },
    {
        "id": "POL-ARCH-07",
        "title": "Build-versus-Buy Review",
        "summary": "Build-versus-buy decisions above 50k USD annual impact require a decision record covering total cost of ownership, security posture, data residency, and an exit strategy.",
        "keywords": ("architecture", "build", "buy", "vendor", "decision", "residency", "review"),
    },
)

_PLAYBOOKS: dict[str, list[str]] = {
    "procurement-approval": [
        "Confirm the request scope and the requesting business owner.",
        "Validate budget authority against the spend threshold policy.",
        "Confirm the vendor security review is current.",
        "Capture legal and data-protection terms that must be in the contract.",
        "Assemble the approval packet with a clear recommendation.",
    ],
    "security-enrichment": [
        "Pull the alert record and confirm severity.",
        "Enrich the identity dimension (accounts, tokens, sessions).",
        "Enrich the endpoint dimension (devices, processes).",
        "Enrich the network dimension (ASNs, destinations).",
        "Assess data-loss indicators and assemble the incident summary.",
    ],
    "claims-exception": [
        "Normalize the claim and identify why it is an exception.",
        "Check the amount against the auto-approval threshold.",
        "Evaluate fraud signals and compliance holds.",
        "Route to the correct specialist (payment, fraud, or compliance).",
        "Draft the customer communication for the decision.",
    ],
    "policy-exception-board": [
        "State the requested exception and the affected policy.",
        "Assess the risk introduced by granting the waiver.",
        "Document the business need and urgency.",
        "Define a compensating control and an expiry date.",
        "Record the board's final recommendation.",
    ],
    "continuity-drill": [
        "Confirm the facility, its criticality, and dependent services.",
        "Plan the drill scope and the participating functions.",
        "Define IT failover and recovery objectives.",
        "Define communications and stakeholder updates.",
        "Define finance and operations contingencies, then schedule the drill.",
    ],
    "loan-origination": [
        "Normalize the application and confirm required documents.",
        "Pull credit and flag scores below the referral threshold.",
        "Verify income and recompute the debt-to-income ratio.",
        "Price the risk tier or refer for manual underwriting per policy.",
        "Assemble the offer packet with conditions and disclosures.",
    ],
    "due-diligence": [
        "Confirm the target profile and the deal thesis.",
        "Run finance, legal, technology, and market workstreams in parallel.",
        "Collect red flags and quantify each one.",
        "Check every red flag for a documented mitigation.",
        "Synthesize a proceed, renegotiate, or walk-away recommendation.",
    ],
    "dispute-resolution": [
        "Capture the dispute, the transaction, and the customer's account of events.",
        "Screen for fraud indicators before any credit decision.",
        "Route to the owning specialist based on the dominant signal.",
        "Resolve per policy and record the provisional credit decision.",
        "Send the customer the outcome and the regulatory-clock status.",
    ],
    "architecture-review": [
        "State the decision, the options, and the deadline.",
        "Score total cost of ownership for each option.",
        "Assess security posture and data residency for each option.",
        "Document the exit strategy for the preferred option.",
        "Record the board's decision with dissents and conditions.",
    ],
    "churn-investigation": [
        "Quantify the anomaly against baseline and segment it.",
        "List candidate causes with their supporting evidence.",
        "Assign specialists to confirm or eliminate each candidate.",
        "Reconcile findings and identify the dominant driver.",
        "Recommend remediation and an early-warning metric.",
    ],
}

_PRIORITY_TIERS: tuple[tuple[int, str], ...] = (
    (80, "critical"),
    (60, "high"),
    (40, "medium"),
    (0, "low"),
)


def _clamp(value: Any, *, low: int = 1, high: int = 5) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = low
    return max(low, min(high, number))


# ---------------------------------------------------------------------------
# Tools.
# ---------------------------------------------------------------------------


@mcp.tool()
def lookup_enterprise_record(record_id: str) -> dict[str, Any]:
    """Look up a single embedded enterprise record by id.

    Returns the record fields, or a ``found: false`` envelope with the list of
    known ids when the record does not exist.
    """

    key = (record_id or "").strip().upper()
    record = _ENTERPRISE_RECORDS.get(key)
    if record is None:
        return {
            "found": False,
            "record_id": record_id,
            "known_ids": sorted(_ENTERPRISE_RECORDS),
        }
    return {"found": True, "record_id": key, **record}


@mcp.tool()
def search_policy(query: str) -> dict[str, Any]:
    """Search the embedded policy catalog with a simple keyword match.

    Ranks policies by how many query terms appear in the title, summary, or
    keyword list. Always returns deterministic results for the same query.
    """

    terms = [term for term in (query or "").lower().replace(",", " ").split() if term]
    scored: list[tuple[int, dict[str, Any]]] = []
    for policy in _POLICY_CATALOG:
        haystack = " ".join((policy["title"], policy["summary"], " ".join(policy["keywords"]))).lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, policy))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    matches = [
        {"id": policy["id"], "title": policy["title"], "summary": policy["summary"], "match_score": score}
        for score, policy in scored
    ]
    return {"query": query, "match_count": len(matches), "matches": matches}


@mcp.tool()
def calculate_priority_score(impact: int, urgency: int, scope: int = 1) -> dict[str, Any]:
    """Compute a deterministic 0-100 priority score and tier.

    ``impact``, ``urgency``, and ``scope`` are clamped to 1-5. The score weights
    impact and urgency more heavily than scope, then maps to a named tier.
    """

    impact_v = _clamp(impact)
    urgency_v = _clamp(urgency)
    scope_v = _clamp(scope)
    raw = (impact_v * 8) + (urgency_v * 8) + (scope_v * 4)  # max 100
    tier = next(name for floor, name in _PRIORITY_TIERS if raw >= floor)
    return {
        "impact": impact_v,
        "urgency": urgency_v,
        "scope": scope_v,
        "score": raw,
        "tier": tier,
    }


@mcp.tool()
def list_playbook_steps(playbook: str) -> dict[str, Any]:
    """Return the ordered steps for an embedded playbook by name."""

    key = (playbook or "").strip().lower().replace("_", "-")
    steps = _PLAYBOOKS.get(key)
    if steps is None:
        return {"found": False, "playbook": playbook, "known_playbooks": sorted(_PLAYBOOKS)}
    return {
        "found": True,
        "playbook": key,
        "step_count": len(steps),
        "steps": [{"order": index, "action": action} for index, action in enumerate(steps, start=1)],
    }


@mcp.tool()
def create_decision_log_entry(
    subject: str,
    decision: str,
    rationale: str = "",
    owner: str = "unassigned",
) -> dict[str, Any]:
    """Return the decision log entry that *would* be recorded.

    This performs no writes. The ``entry_id`` is a deterministic hash of the
    inputs so the same decision always produces the same id, which keeps tests
    and notebook runs reproducible.
    """

    fingerprint = "|".join((subject or "", decision or "", rationale or "", owner or ""))
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
    return {
        "persisted": False,
        "entry_id": f"DLOG-{digest}",
        "subject": subject,
        "decision": decision,
        "rationale": rationale,
        "owner": owner,
    }


def list_tool_names() -> tuple[str, ...]:
    """Return the names of every tool registered on this server.

    Reads the live FastMCP tool registry so callers (and tests) can verify what
    the stdio server actually exposes without spawning a subprocess.
    """

    return tuple(sorted(tool.name for tool in mcp._tool_manager.list_tools()))


AVAILABLE_TOOLS: tuple[str, ...] = list_tool_names()


def main() -> None:
    """Run the server over stdio."""

    mcp.run("stdio")


if __name__ == "__main__":
    main()
