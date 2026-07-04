from __future__ import annotations

import importlib
import json
import sys
import textwrap
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PROJECTS = (
    {
        "folder": "responses-api-scenarios",
        "package": "release_room",
        "api_name": "Responses API",
        "api_boundary": "Responses API /responses",
        "input_label": "OpenAI-style input",
        "output_label": "Responses output",
        "sample_attr": "sample_input",
        "payload_name": "RESPONSES_PAYLOAD",
    },
    {
        "folder": "invocations-api-scenarios",
        "package": "review_bot",
        "api_name": "Invocations API",
        "api_boundary": "Invocations API /invocations",
        "input_label": "Job payload",
        "output_label": "Invocation summary",
        "sample_attr": "sample_task",
        "payload_name": "INVOCATION_PAYLOAD",
    },
)


PATTERN_DOCS = {
    "sequential": (
        "Sequential orchestration is a fixed pipeline. Each agent receives the original request plus the "
        "work accumulated so far, so the output should read like a controlled handoff from stage to stage.",
        "Best fit: repeatable workflows where every request needs the same ordered checks."
    ),
    "concurrent": (
        "Concurrent orchestration fans one request out to several specialists. They work independently, "
        "then a code-defined fan-in executor labels and combines their findings. Scenarios with a "
        "designated synthesizer hold that agent out of the fan-out and run it after fan-in, so the agent "
        "that combines the perspectives actually sees them.",
        "Best fit: independent reviews where parallel perspectives are more valuable than turn-taking."
    ),
    "handoff": (
        "Handoff orchestration starts with triage, which names the owning specialist with a ROUTE directive. "
        "A code-defined router validates that choice against the allowed routes (falling back to keyword "
        "scoring), and scenarios with a designated finisher always end with that fixed owner completing the work.",
        "Best fit: support, claims, entitlement, and exception flows where ownership depends on context."
    ),
    "group-chat": (
        "Group chat orchestration creates a visible multi-agent discussion. A selector function chooses the "
        "next participant and a termination function decides when the discussion is good enough.",
        "Best fit: decisions that benefit from critique, tradeoffs, and a short transcript."
    ),
    "magentic": (
        "Magentic orchestration uses a manager agent to plan, delegate, monitor progress, and replan when "
        "the work stalls. It is intentionally more open-ended than the other patterns.",
        "Best fit: ambiguous work where the system must decide which specialists to involve and in what order."
    ),
}


PATTERN_ANATOMY = {
    "sequential": {
        "control_flow": "Agents run in a fixed order, with each stage receiving the prior stage response.",
        "coordination": "The graph defines the chain. The model does not decide which agent acts next.",
        "output_behavior": "The terminal output includes the stage transcript.",
        "best_when": "Use for repeatable pipelines where every request needs the same stages.",
    },
    "concurrent": {
        "control_flow": "Parallel lanes receive the same input and run independently; an optional synthesizer runs after fan-in.",
        "coordination": "The graph fans out work, aggregates labelled outputs, and can forward them to a synthesis agent.",
        "output_behavior": "Each lane contributes a labelled perspective; a synthesizer combines them when declared.",
        "best_when": "Use when independent reviews can happen in parallel.",
    },
    "handoff": {
        "control_flow": "Triage names a ROUTE, the router validates it, one specialist runs (plus an optional fixed finisher).",
        "coordination": "The router honors the triage ROUTE directive and falls back to keyword scoring.",
        "output_behavior": "The output identifies the route, its source (directive or keywords), and the answers.",
        "best_when": "Use when the right owner depends on the request.",
    },
    "group-chat": {
        "control_flow": "Agents take turns until a termination condition is met.",
        "coordination": "A selector function chooses the next participant.",
        "output_behavior": "The transcript shows critique, refinement, and convergence.",
        "best_when": "Use when visible debate improves the answer.",
    },
    "magentic": {
        "control_flow": "A manager plans work and delegates dynamically to specialists.",
        "coordination": "The manager replans as the task evolves or stalls.",
        "output_behavior": "Specialist outputs show the manager-led investigation path.",
        "best_when": "Use for open-ended work that needs planning and replanning.",
    },
}

PATTERN_LIVE_RUN_INTRO = {
    "sequential": (
        "Each agent output is captured by a `StageGateExecutor` and appended to a growing "
        "transcript. The next agent receives both the original prompt and the accumulated "
        "work so far. The final cell prints the complete stage-by-stage log."
    ),
    "concurrent": (
        "The request fans out to the parallel lanes simultaneously. A fan-in executor waits for "
        "every response and labels each contribution. Without a synthesizer the labelled findings "
        "are the output; with one, a `ConcurrentSynthesisGateExecutor` forwards them to the "
        "synthesis agent, which produces the final deliverable. Execution order inside the "
        "fan-out is non-deterministic."
    ),
    "handoff": (
        "Triage runs first and ends with a `ROUTE: <AgentName>` line. The `HandoffRouterExecutor` "
        "honors that directive when it names an allowed route, otherwise it scores each specialist "
        "keyword list against the triage text. If the scenario declares a finisher, the routed "
        "specialist's notes flow to that fixed agent, which completes the deliverable. The output "
        "shows the route taken and whether it came from the model directive or keyword fallback."
    ),
    "group-chat": (
        "Participants speak in round-robin order. The termination function fires when an "
        "approved recommendation appears or after seven assistant turns. Intermediate outputs "
        "from each participant are surfaced alongside the final transcript."
    ),
    "magentic": (
        "The manager agent plans, delegates to specialists, and replans if work stalls or "
        "reaches a reset limit. With `max_round_count=10`, `max_stall_count=3`, and "
        "`max_reset_count=2`, there is room to iterate. Allow extra time -- this pattern "
        "runs more LLM calls than the others."
    ),
}


PATTERN_INSPECT = {
    "sequential": (
        "Compare the first stage output to the final editor output. Later stages should "
        "build on prior work, not repeat it -- each `StageGateExecutor` carries the full "
        "transcript forward. If a stage ignores prior context, inspect its instructions "
        "and the gate prompt to see exactly what the agent received."
    ),
    "concurrent": (
        "Check that each labelled lane contribution is non-overlapping. Because lanes "
        "receive the same input and run independently, their findings should be additive, "
        "not redundant. When the scenario declares a synthesizer, confirm its final entry "
        "actually reconciles the labelled findings above it rather than repeating one lane."
    ),
    "handoff": (
        "Verify the route matches the triage intent, and check the route source in the output "
        "header: 'model-directive' means the triage agent's ROUTE line was honored; "
        "'keyword-score' means the router fell back to scoring keywords. Try rewording the "
        "input toward a different specialist domain and rerun -- the route should change. "
        "Inspect `ctx.get_state('route')` and `ctx.get_state('route_source')` in the workflow state."
    ),
    "group-chat": (
        "Read the transcript chronologically. Later turns should respond to earlier critiques "
        "rather than restarting the discussion. The termination function fires on 'approved' "
        "plus 'recommendation' in the same message, or after seven assistant turns -- check "
        "which condition fired and why."
    ),
    "magentic": (
        "Follow the specialist outputs to reconstruct the manager delegation path. If the "
        "manager replanned, you will see the same specialist invoked more than once or a "
        "different specialist substituted mid-run. A stall (no progress for max_stall_count "
        "rounds) triggers a reset; a second stall terminates the workflow."
    ),
}


def cell_source(source: str) -> list[str]:
    text = textwrap.dedent(source).strip("\n")
    lines = text.splitlines()
    first = next((line for line in lines if line.strip()), "")
    if first.startswith("    "):
        lines = [line[4:] if line.startswith("    ") else line for line in lines]
    return [f"{line}\n" for line in lines]


def md(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": cell_source(source)}


def code(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": cell_source(source),
    }


def add_cell_ids(cells: list[dict[str, Any]], scenario_id: str) -> None:
    safe_id = "".join(char if char.isalnum() or char == "-" else "-" for char in scenario_id)
    prefix = safe_id[:56].strip("-") or "scenario"
    for index, cell in enumerate(cells):
        cell["id"] = f"{prefix}-{index:02d}"


def load_scenarios(project: dict[str, str]) -> tuple[Any, ...]:
    src = ROOT / project["folder"] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    module = importlib.import_module(f"{project['package']}.scenarios")
    return tuple(module.SCENARIOS)


def notebook_paths_by_id(project: dict[str, str], scenarios: tuple[Any, ...]) -> dict[str, Path]:
    scenario_ids = {scenario.id for scenario in scenarios}
    result: dict[str, Path] = {}
    for path in sorted((ROOT / project["folder"] / "notebooks").glob("*.ipynb")):
        text = path.read_text(encoding="utf-8")
        matches = [scenario_id for scenario_id in scenario_ids if scenario_id in text]
        if len(matches) != 1:
            raise RuntimeError(f"Could not identify scenario for {path}: {matches}")
        result[matches[0]] = path
    missing = scenario_ids - set(result)
    if missing:
        raise RuntimeError(f"Missing notebooks for {sorted(missing)}")
    return result


def scenario_data(scenario: Any, sample_attr: str) -> dict[str, Any]:
    return {
        "id": scenario.id,
        "pattern": scenario.pattern,
        "title": scenario.title,
        "learning_goal": scenario.learning_goal,
        "when_to_use": scenario.when_to_use,
        sample_attr: getattr(scenario, sample_attr),
        "handoff_finisher": getattr(scenario, "handoff_finisher", None),
        "concurrent_synthesizer": getattr(scenario, "concurrent_synthesizer", None),
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "instructions": agent.instructions,
                "mcp_tools": list(agent.mcp_tools),
                "mcp_server": agent.mcp_server,
                "route_keywords": list(getattr(agent, "route_keywords", ()) or ()),
            }
            for agent in scenario.agents
        ],
    }


def scenario_uses_mcp(scenario: Any) -> bool:
    return any(agent.mcp_tools for agent in scenario.agents)


def scenario_mcp_server(scenario: Any) -> str | None:
    servers = {agent.mcp_server for agent in scenario.agents if agent.mcp_tools}
    if not servers:
        return None
    if len(servers) != 1:
        raise RuntimeError(f"{scenario.id} uses multiple MCP servers: {servers}")
    return next(iter(servers))


def _agent_capability_label(agent: Any) -> str:
    """Short display string of agent capabilities for the roster table."""
    mcp_tools = list(getattr(agent, "mcp_tools", ()) or ())
    if mcp_tools:
        return "Domain tools: " + ", ".join("`" + t + "`" for t in mcp_tools)
    return "Instructions only"


def title_markdown(project: dict[str, str], scenario: Any) -> str:
    return f"""
    # {scenario.title}

    | Field | Value |
    | --- | --- |
    | Scenario id | `{scenario.id}` |
    | Pattern | `{scenario.pattern}` |
    | API | `{project['api_name']}` |

    **Learning goal:** {scenario.learning_goal}

    > {scenario.when_to_use}
    """


def concept_markdown(project: dict[str, str], scenario: Any) -> str:
    concept, best_fit = PATTERN_DOCS[scenario.pattern]

    if project["sample_attr"] == "sample_input":
        api_note = (
            "**Responses API -- startup-selected scenario shape.** "
            "The scenario and orchestration pattern are wired in at server start. "
            "Each client request uses the standard OpenAI-compatible `/responses` body -- "
            "a plain chat-style input. The client never specifies which agents run; "
            "the server owns the orchestration entirely."
        )
    else:
        api_note = (
            "**Invocations API -- per-request job payload shape.** "
            "Each request body carries `scenario`, `pattern`, `task`, `artifacts`, and "
            "`constraints`. The caller controls which orchestration runs per invocation. "
            "This fits webhooks, CI pipelines, schedulers, and service-to-service calls "
            "where the task definition changes with every request."
        )

    if scenario.id.startswith("scenario-16-quote-to-cash"):
        story = (
            "This is a Scenario 16 quote-to-cash variant. The same six business roles "
            "(CRM trigger, customer context, SKU discovery, product fit, pricing and legal, "
            "quote generation) appear in every Scenario 16 notebook -- only the orchestration "
            "pattern changes. Compare notebooks 16a-16e to see how the same roles behave "
            "under sequential, concurrent, handoff, group-chat, and magentic coordination."
        )
    elif scenario_uses_mcp(scenario):
        story = (
            "This is an enterprise scenario grounded by deterministic MCP context tools. "
            "In production those tools are served by a FastMCP stdio subprocess; "
            "this notebook inlines the same functions as plain callables so it runs "
            "without a local package or subprocess."
        )
    else:
        story = (
            "This is a starter scenario. The domain is intentionally lightweight "
            "so the orchestration mechanics are easy to trace before the enterprise "
            "and quote-to-cash notebooks layer in MCP tool calls and richer context."
        )

    anatomy = PATTERN_ANATOMY[scenario.pattern]
    anatomy_rows = "\n".join([
        "| Dimension | Detail |",
        "| --- | --- |",
        "| Control flow | " + anatomy["control_flow"] + " |",
        "| Coordination | " + anatomy["coordination"] + " |",
        "| Output | " + anatomy["output_behavior"] + " |",
        "| Best when | " + anatomy["best_when"] + " |",
    ])

    agent_header = "| Agent | Role | Capabilities |\n| --- | --- | --- |"
    agent_lines = "\n".join(
        "| `" + a.name + "` | " + a.description + " | " + _agent_capability_label(a) + " |"
        for a in scenario.agents
    )
    agent_table = agent_header + "\n" + agent_lines

    pattern_heading = scenario.pattern.replace("-", " ").title()

    return f"""
    ## Pattern: {pattern_heading}

    {concept}

    {best_fit}

    ## API Shape

    {api_note}

    {story}

    ## Pattern Anatomy

    {anatomy_rows}

    ## Instruction-Led LLM Agents

    {agent_table}

    > **Instructor note:** Each row is an LLM-backed agent with role instructions.
    > Most agents rely on instructions alone; enterprise and quote-to-cash agents may
    > also call domain tools for grounded context.
    """


def environment_cell() -> str:
    return r'''
    import os

    from IPython.display import HTML, display


    _APTOS_STYLE = """
    <style>
    :root { --jp-content-font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif; }
    .jp-RenderedHTMLCommon, .jp-RenderedMarkdown, .rendered_html, .jp-OutputArea-output {
        font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif;
        line-height: 1.55;
    }
    .jp-RenderedHTMLCommon h1, .jp-RenderedHTMLCommon h2, .jp-RenderedHTMLCommon h3 {
        font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    </style>
    """


    def apply_notebook_style() -> str:
        display(HTML(_APTOS_STYLE))
        return _APTOS_STYLE


    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:14b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MCP_TOOL_FUNCTIONS: dict[str, object] = {}

    apply_notebook_style()
    print(f"Ollama target: {OLLAMA_HOST} / {OLLAMA_MODEL}")
    '''


def mcp_markdown(server: str | None) -> str:
    if server == "quote_to_cash_context":
        label = "quote-to-cash context"
    else:
        label = "enterprise context"
    return f"""
    ## MCP Tool Context

    In production, these {label} functions are exposed by a local FastMCP stdio server and attached to
    instruction-led LLM agents with `MCPStdioTool` using per-agent allowed tools. This notebook inlines
    the same domain functions as plain callable tools so it remains standalone.
    """


def enterprise_tools_cell() -> str:
    return r'''
    import hashlib
    from typing import Any, Sequence


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
            "summary": "Risk waivers require a documented business need, a compensating control, and a fixed expiry.",
            "keywords": ("policy", "exception", "waiver", "risk", "compliance", "governance", "residency"),
        },
        {
            "id": "POL-BCP-02",
            "title": "Business Continuity Drills",
            "summary": "Tier-1 facilities must complete a continuity drill at least every 365 days.",
            "keywords": ("continuity", "drill", "facility", "tier-1", "operations", "recovery"),
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
            "Enrich the identity dimension.",
            "Enrich the endpoint dimension.",
            "Enrich the network dimension.",
            "Assess data-loss indicators and assemble the incident summary.",
        ],
        "claims-exception": [
            "Normalize the claim and identify why it is an exception.",
            "Check the amount against the auto-approval threshold.",
            "Evaluate fraud signals and compliance holds.",
            "Route to the correct specialist.",
            "Draft the customer communication.",
        ],
        "policy-exception-board": [
            "State the requested exception and the affected policy.",
            "Assess the introduced risk.",
            "Document the business need and urgency.",
            "Define a compensating control and expiry date.",
            "Record the board recommendation.",
        ],
        "continuity-drill": [
            "Confirm the facility, criticality, and dependent services.",
            "Plan the drill scope and participants.",
            "Define IT failover and recovery objectives.",
            "Define communications and stakeholder updates.",
            "Define finance and operations contingencies.",
        ],
    }

    _PRIORITY_TIERS: tuple[tuple[int, str], ...] = (
        (80, "critical"),
        (60, "high"),
        (40, "medium"),
        (0, "low"),
    )


    def _clamp(value: Any, low: int = 1, high: int = 5) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = low
        return max(low, min(high, number))


    def lookup_enterprise_record(record_id: str) -> dict[str, Any]:
        """Look up a single embedded enterprise record by id."""

        key = (record_id or "").strip().upper()
        record = _ENTERPRISE_RECORDS.get(key)
        if record is None:
            return {"found": False, "record_id": record_id, "known_ids": sorted(_ENTERPRISE_RECORDS)}
        return {"found": True, "record_id": key, **record}


    def search_policy(query: str) -> dict[str, Any]:
        """Search the embedded policy catalog with a simple keyword match."""

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


    def calculate_priority_score(impact: int, urgency: int, scope: int = 1) -> dict[str, Any]:
        """Compute a deterministic 0-100 priority score and tier."""

        impact_v = _clamp(impact)
        urgency_v = _clamp(urgency)
        scope_v = _clamp(scope)
        raw = (impact_v * 8) + (urgency_v * 8) + (scope_v * 4)
        tier = next(name for floor, name in _PRIORITY_TIERS if raw >= floor)
        return {"impact": impact_v, "urgency": urgency_v, "scope": scope_v, "score": raw, "tier": tier}


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


    def create_decision_log_entry(
        subject: str,
        decision: str,
        rationale: str = "",
        owner: str = "unassigned",
    ) -> dict[str, Any]:
        """Return the decision log entry that would be recorded."""

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


    MCP_TOOL_FUNCTIONS.update(
        {
            "lookup_enterprise_record": lookup_enterprise_record,
            "search_policy": search_policy,
            "calculate_priority_score": calculate_priority_score,
            "list_playbook_steps": list_playbook_steps,
            "create_decision_log_entry": create_decision_log_entry,
        }
    )
    '''


def quote_to_cash_tools_cell() -> str:
    return r'''
    import hashlib
    from typing import Any


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
            "trigger_conditions": ["Opportunity stage is Negotiation or later."],
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
    _INCOMPATIBLE_PAIRS = {("SKU-ROUTE-OPT", "SKU-ANALYTICS-EDGE")}
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
            "clauses": ["Net-30 payment terms.", "Click-through terms acceptable below $50k."],
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


    def crm_get_quote_trigger(opportunity_id: str = "OPP-5001") -> dict[str, Any]:
        """Return CRM trigger state for an opportunity."""

        key = (opportunity_id or "").strip().upper()
        record = _QUOTE_TRIGGERS.get(key)
        if record is None:
            return {"found": False, "opportunity_id": opportunity_id, "known_ids": sorted(_QUOTE_TRIGGERS)}
        return {"found": True, **record}


    def crm_get_customer_profile(account_id: str = "ACC-3300") -> dict[str, Any]:
        """Return the enriched CRM customer profile for an account."""

        key = (account_id or "").strip().upper()
        record = _CUSTOMER_PROFILES.get(key)
        if record is None:
            return {"found": False, "account_id": account_id, "known_ids": sorted(_CUSTOMER_PROFILES)}
        return {"found": True, **record}


    def product_search_catalog(query: str = "analytics platform") -> dict[str, Any]:
        """Search the product/SKU catalog with a simple keyword match."""

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


    def product_validate_skus(skus: str = "") -> dict[str, Any]:
        """Validate SKU compatibility, availability, and completeness."""

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


    def pricing_calculate_quote(skus: str = "", discount_pct: float = 0.0) -> dict[str, Any]:
        """Calculate quote pricing for a set of SKUs."""

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


    def quote_format_package(
        customer_name: str = "Contoso Manufacturing",
        total: float = 0.0,
        skus: str = "",
    ) -> dict[str, Any]:
        """Format the final customer-ready quote package."""

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


    MCP_TOOL_FUNCTIONS.update(
        {
            "crm_get_quote_trigger": crm_get_quote_trigger,
            "crm_get_customer_profile": crm_get_customer_profile,
            "product_search_catalog": product_search_catalog,
            "product_validate_skus": product_validate_skus,
            "pricing_calculate_quote": pricing_calculate_quote,
            "legal_evaluate_terms": legal_evaluate_terms,
            "quote_format_package": quote_format_package,
        }
    )
    '''


def agent_factory_cell() -> str:
    return r'''
    from dataclasses import dataclass
    from typing import Any

    from agent_framework.ollama import OllamaChatClient


    DEFAULT_OLLAMA_TEMPERATURE = 0.0
    DEFAULT_OLLAMA_NUM_CTX = 8192
    DEFAULT_OLLAMA_KEEP_ALIVE = "10m"
    DEFAULT_OLLAMA_THINK = False

    _UNSUPPORTED_OLLAMA_CHAT_OPTIONS = {
        "allow_multiple_tool_calls",
        "conversation_id",
        "logit_bias",
        "metadata",
        "store",
        "user",
    }


    @dataclass(frozen=True)
    class OllamaAgentConfig:
        model: str
        host: str
        temperature: float
        num_ctx: int
        max_tokens: int
        keep_alive: str
        think: bool

        def default_options(self) -> dict[str, Any]:
            return {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "max_tokens": self.max_tokens,
                "keep_alive": self.keep_alive,
                "think": self.think,
            }


    def parse_env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None or value.strip() == "":
            return default
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"{name} must be true or false.")


    def build_ollama_config(
        *,
        model: str | None = None,
        host: str | None = None,
        temperature: float | None = None,
        num_ctx: int | None = None,
        max_tokens: int | None = None,
        keep_alive: str | None = None,
        think: bool | None = None,
    ) -> OllamaAgentConfig:
        return OllamaAgentConfig(
            model=model or os.getenv("OLLAMA_MODEL") or "qwen3:14b",
            host=host or os.getenv("OLLAMA_HOST") or "http://localhost:11434",
            temperature=temperature
            if temperature is not None
            else float(os.getenv("OLLAMA_TEMPERATURE", str(DEFAULT_OLLAMA_TEMPERATURE))),
            num_ctx=num_ctx if num_ctx is not None else int(os.getenv("OLLAMA_NUM_CTX", str(DEFAULT_OLLAMA_NUM_CTX))),
            max_tokens=max_tokens if max_tokens is not None else int(os.getenv("OLLAMA_MAX_TOKENS", "500")),
            keep_alive=keep_alive or os.getenv("OLLAMA_KEEP_ALIVE") or DEFAULT_OLLAMA_KEEP_ALIVE,
            think=think if think is not None else parse_env_bool("OLLAMA_THINK", DEFAULT_OLLAMA_THINK),
        )


    class ScenarioOllamaChatClient(OllamaChatClient):
        def _prepare_options(self, messages: Any, options: Any) -> dict[str, Any]:
            filtered = {
                key: value
                for key, value in dict(options).items()
                if key not in _UNSUPPORTED_OLLAMA_CHAT_OPTIONS
            }
            return super()._prepare_options(messages, filtered)


    def make_agent(spec: Any, *, config: OllamaAgentConfig | None = None) -> Any:
        resolved = config or build_ollama_config()
        instructions = f"You are {spec.name}. {spec.instructions}"
        tools = tools_for_agent(spec)
        return ScenarioOllamaChatClient(host=resolved.host, model=resolved.model).as_agent(
            name=spec.name,
            description=spec.description,
            instructions=instructions,
            tools=tools or None,
            default_options=resolved.default_options(),
            require_per_service_call_history_persistence=True,
        )
    '''


def scenario_cell(project: dict[str, str], data: dict[str, Any]) -> str:
    sample_attr = project["sample_attr"]
    scenario_json = textwrap.indent(json.dumps(data, indent=2), "    ")
    sample_prompt = (
        "SAMPLE_PROMPT = SCENARIO.sample_input"
        if sample_attr == "sample_input"
        else "SAMPLE_PROMPT = build_invocation_prompt(INVOCATION_PAYLOAD)"
    )
    payload = (
        '    RESPONSES_PAYLOAD = {"input": SCENARIO.sample_input, "stream": False}'
        if sample_attr == "sample_input"
        else textwrap.indent(
            textwrap.dedent(
                '''
            INVOCATION_PAYLOAD = {
                "scenario": SCENARIO.id,
                "pattern": SCENARIO.pattern,
                "task": SCENARIO.sample_task,
                "subject": "notebook sample",
                "artifacts": [],
                "constraints": [],
                "stream": False,
            }
            '''
            ).strip(),
            "    ",
        )
    )
    invocation_prompt = (
        ""
        if sample_attr == "sample_input"
        else textwrap.indent(
            textwrap.dedent(
                r'''


                def build_invocation_prompt(payload: dict[str, object]) -> str:
                    artifacts = "\n".join(f"- {item}" for item in payload.get("artifacts", [])) or "- No artifacts supplied."
                    constraints = "\n".join(f"- {item}" for item in payload.get("constraints", [])) or "- No explicit constraints."
                    return (
                        f"Scenario: {payload['scenario']} - {SCENARIO.title}\n"
                        f"Pattern: {payload['pattern']}\n"
                        f"Learning goal: {SCENARIO.learning_goal}\n"
                        f"Subject: {payload['subject']}\n"
                        f"Task: {payload['task']}\n\n"
                        f"Artifacts:\n{artifacts}\n\n"
                        f"Constraints:\n{constraints}\n\n"
                        "Session context:\nNo prior turns for this session.\n\n"
                        "Return actionable findings. Do not claim to have inspected artifacts beyond the provided names and context."
                    )
                '''
            ).strip("\n"),
            "    ",
        )
    )
    return f'''
    import json
    from dataclasses import dataclass
    from typing import Any, Sequence


    @dataclass(frozen=True)
    class AgentSpec:
        name: str
        description: str
        instructions: str
        mcp_tools: tuple[str, ...] = ()
        mcp_server: str = "enterprise_context"
        route_keywords: tuple[str, ...] = ()


    @dataclass(frozen=True)
    class ScenarioSpec:
        id: str
        pattern: str
        title: str
        learning_goal: str
        when_to_use: str
        {sample_attr}: str
        agents: tuple[AgentSpec, ...]
        handoff_finisher: str | None = None
        concurrent_synthesizer: str | None = None


    SCENARIO_DATA = json.loads(
        r"""
{scenario_json}
        """
    )
    AGENTS = tuple(
        AgentSpec(
            name=item["name"],
            description=item["description"],
            instructions=item["instructions"],
            mcp_tools=tuple(item.get("mcp_tools", [])),
            mcp_server=item.get("mcp_server", "enterprise_context"),
            route_keywords=tuple(item.get("route_keywords", [])),
        )
        for item in SCENARIO_DATA["agents"]
    )
    SCENARIO = ScenarioSpec(
        id=SCENARIO_DATA["id"],
        pattern=SCENARIO_DATA["pattern"],
        title=SCENARIO_DATA["title"],
        learning_goal=SCENARIO_DATA["learning_goal"],
        when_to_use=SCENARIO_DATA["when_to_use"],
        {sample_attr}=SCENARIO_DATA["{sample_attr}"],
        agents=AGENTS,
        handoff_finisher=SCENARIO_DATA.get("handoff_finisher"),
        concurrent_synthesizer=SCENARIO_DATA.get("concurrent_synthesizer"),
    )


    def tools_for_agent(spec: AgentSpec) -> list[object]:
        tools: list[object] = []
        for tool_name in spec.mcp_tools:
            try:
                tools.append(MCP_TOOL_FUNCTIONS[tool_name])
            except KeyError as exc:
                raise ValueError(f"Missing inlined tool '{{tool_name}}' for {{spec.name}}.") from exc
        return tools


    def scenario_summary(scenario: ScenarioSpec) -> dict[str, str]:
        return {{
            "id": scenario.id,
            "title": scenario.title,
            "pattern": scenario.pattern,
            "learning_goal": scenario.learning_goal,
            "when_to_use": scenario.when_to_use,
            "sample": getattr(scenario, "{sample_attr}"),
        }}


    def agent_capability_map(scenario: ScenarioSpec) -> list[dict[str, Any]]:
        return [
            {{
                "agent": spec.name,
                "description": spec.description,
                "instructions": spec.instructions,
                "mcp_tools": list(spec.mcp_tools),
                "mcp_server": spec.mcp_server if spec.mcp_tools else None,
            }}
            for spec in scenario.agents
        ]


    def mcp_tool_context(scenario: ScenarioSpec) -> dict[str, Any]:
        tools_by_agent = {{spec.name: list(spec.mcp_tools) for spec in scenario.agents if spec.mcp_tools}}
        all_tools_used = sorted({{tool for spec in scenario.agents for tool in spec.mcp_tools}})
        return {{
            "uses_mcp": bool(all_tools_used),
            "tools_by_agent": tools_by_agent,
            "all_tools_used": all_tools_used,
        }}
{invocation_prompt}

    MAX_TOKENS = 500 if SCENARIO.pattern == "magentic" else 250
{payload}
    {sample_prompt}

    print(json.dumps(scenario_summary(SCENARIO), indent=2))
    print(json.dumps(agent_capability_map(SCENARIO), indent=2))
    if mcp_tool_context(SCENARIO)["uses_mcp"]:
        print(json.dumps(mcp_tool_context(SCENARIO), indent=2))
    '''


def workflow_cell() -> str:
    return r'''
    import re
    from collections.abc import Mapping
    from typing import Never

    from agent_framework import (
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        Executor,
        Message,
        WorkflowBuilder,
        WorkflowContext,
        handler,
    )


    _TRANSCRIPT_KEY = "transcript"
    _STOPWORDS = {"agent", "specialist", "the", "and", "for", "with", "that", "from", "into"}


    def make_request(text: str) -> AgentExecutorRequest:
        return AgentExecutorRequest(messages=[Message(role="user", contents=[text])])


    def response_text(response: AgentExecutorResponse) -> str:
        agent_response = getattr(response, "agent_response", None)
        return (getattr(agent_response, "text", None) or "").strip()


    def _append_transcript(ctx: WorkflowContext[Any], author: str, text: str) -> list[str]:
        transcript = list(ctx.get_state(_TRANSCRIPT_KEY) or [])
        transcript.append(f"[{author}] {text}")
        ctx.set_state(_TRANSCRIPT_KEY, transcript)
        return transcript


    class PromptDispatchExecutor(Executor):
        @handler
        async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            ctx.set_state("prompt", prompt)
            ctx.set_state(_TRANSCRIPT_KEY, [])
            await ctx.send_message(make_request(prompt))


    class StageGateExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(transcript)
            await ctx.send_message(make_request(f"Original request:\n{prompt}\n\nWork so far:\n{carried}"))


    class SequentialOutputExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            await ctx.yield_output("\n\n".join(transcript))


    class ConcurrentAggregatorExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names

        @handler
        async def aggregate(self, responses: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]) -> None:
            labelled: list[str] = []
            for index, response in enumerate(responses):
                name = self._agent_names[index] if index < len(self._agent_names) else f"agent{index + 1}"
                labelled.append(f"[{name}]\n{response_text(response)}")
            await ctx.yield_output("\n\n".join(labelled))


    class ConcurrentSynthesisGateExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names

        @handler
        async def gate(self, responses: list[AgentExecutorResponse], ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            for index, response in enumerate(responses):
                name = self._agent_names[index] if index < len(self._agent_names) else f"agent{index + 1}"
                _append_transcript(ctx, name, response_text(response))
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(ctx.get_state(_TRANSCRIPT_KEY) or [])
            await ctx.send_message(
                make_request(
                    f"You are the synthesis stage.\nOriginal request:\n{prompt}\n\n"
                    f"Independent specialist findings:\n{carried}\n\n"
                    "Combine these findings into the final deliverable."
                )
            )


    _ROUTE_DIRECTIVE = re.compile(r"route\s*:\s*([A-Za-z][A-Za-z0-9 _-]*)", re.IGNORECASE)


    def _route_slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


    class HandoffRouterExecutor(Executor):
        def __init__(
            self,
            id: str,
            *,
            routes: dict[str, tuple[str, ...]],
            default_route: str,
            display_names: dict[str, str] | None = None,
        ) -> None:
            super().__init__(id=id)
            self._routes = routes
            self._default_route = default_route
            self._display_names = display_names or {}

        def directed(self, text: str) -> str | None:
            for match in reversed(_ROUTE_DIRECTIVE.findall(text)):
                slug = _route_slug(match)
                if slug in self._routes:
                    return slug
            return None

        def choose(self, text: str) -> str:
            directed = self.directed(text)
            if directed is not None:
                return directed
            lowered = text.lower()
            best_route, best_hits = self._default_route, 0
            for route, keywords in self._routes.items():
                hits = sum(1 for keyword in keywords if keyword in lowered)
                if hits > best_hits:
                    best_route, best_hits = route, hits
            return best_route

        @handler
        async def route(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            triage_text = response_text(response)
            chosen = self.choose(triage_text)
            ctx.set_state("route", chosen)
            ctx.set_state("route_name", self._display_names.get(chosen, chosen))
            ctx.set_state("route_source", "model-directive" if self.directed(triage_text) else "keyword-score")
            prompt = ctx.get_state("prompt") or ""
            await ctx.send_message(
                make_request(f"Triage routed this to you.\nRequest:\n{prompt}\n\nTriage notes:\n{triage_text}"),
                target_id=chosen,
            )


    class HandoffFinisherGateExecutor(Executor):
        @handler
        async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            route = ctx.get_state("route_name") or ctx.get_state("route") or "specialist"
            transcript = _append_transcript(ctx, route, response_text(response))
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(transcript)
            await ctx.send_message(
                make_request(
                    f"You are the finishing stage of a handoff.\nOriginal request:\n{prompt}\n\n"
                    f"Routed specialist notes:\n{carried}\n\nComplete the final deliverable."
                )
            )


    class HandoffOutputExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str | None = None) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            route = ctx.get_state("route_name") or ctx.get_state("route") or "specialist"
            source = ctx.get_state("route_source") or "keyword-score"
            header = f"[routed to {route} via {source}]"
            if self._stage_name is None:
                await ctx.yield_output(f"{header}\n{response_text(response)}")
                return
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            await ctx.yield_output("\n\n".join([header, *transcript]))


    def _slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


    def _agents_for(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> list[Any]:
        return [make_agent(spec, config=config) for spec in scenario.agents]


    def _agent_executor(spec_index: int, scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> AgentExecutor:
        spec = scenario.agents[spec_index]
        return AgentExecutor(make_agent(spec, config=config), id=_slug(spec.name))


    def _route_keywords(spec: AgentSpec) -> tuple[str, ...]:
        if spec.route_keywords:
            return tuple(spec.route_keywords)
        tokens = re.findall(r"[a-z]+", f"{spec.name} {spec.description}".lower())
        keywords = [token for token in tokens if len(token) > 3 and token not in _STOPWORDS]
        return tuple(dict.fromkeys(keywords))[:6]


    def build_sequential_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        agents = [_agent_executor(i, scenario, config=config) for i in range(len(scenario.agents))]
        dispatch = PromptDispatchExecutor(id="dispatch")
        output = SequentialOutputExecutor(id="final_output", stage_name=scenario.agents[-1].name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_edge(dispatch, agents[0])
        for index in range(len(agents) - 1):
            gate = StageGateExecutor(id=f"gate_{index}", stage_name=scenario.agents[index].name)
            builder.add_edge(agents[index], gate)
            builder.add_edge(gate, agents[index + 1])
        builder.add_edge(agents[-1], output)
        return builder.build()


    def build_concurrent_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        synthesizer_name = scenario.concurrent_synthesizer
        parallel = [i for i in range(len(scenario.agents)) if scenario.agents[i].name != synthesizer_name]
        agents = [_agent_executor(i, scenario, config=config) for i in parallel]
        parallel_names = [scenario.agents[i].name for i in parallel]
        dispatch = PromptDispatchExecutor(id="dispatch")
        if synthesizer_name is None:
            aggregator = ConcurrentAggregatorExecutor(id="aggregator", agent_names=parallel_names)
            builder = WorkflowBuilder(start_executor=dispatch, output_from=[aggregator])
            builder.add_fan_out_edges(dispatch, agents)
            builder.add_fan_in_edges(agents, aggregator)
            return builder.build()
        synthesizer_index = next(
            i for i in range(len(scenario.agents)) if scenario.agents[i].name == synthesizer_name
        )
        synthesizer = _agent_executor(synthesizer_index, scenario, config=config)
        gate = ConcurrentSynthesisGateExecutor(id="synthesis_gate", agent_names=parallel_names)
        output = SequentialOutputExecutor(id="final_output", stage_name=synthesizer_name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_fan_out_edges(dispatch, agents)
        builder.add_fan_in_edges(agents, gate)
        builder.add_edge(gate, synthesizer)
        builder.add_edge(synthesizer, output)
        return builder.build()


    def build_handoff_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        triage = _agent_executor(0, scenario, config=config)
        finisher_name = scenario.handoff_finisher
        routable = [i for i in range(1, len(scenario.agents)) if scenario.agents[i].name != finisher_name]
        specialists = [_agent_executor(i, scenario, config=config) for i in routable]
        specialist_ids = [_slug(scenario.agents[i].name) for i in routable]
        routes = {specialist_ids[pos]: _route_keywords(scenario.agents[i]) for pos, i in enumerate(routable)}
        display_names = {specialist_ids[pos]: scenario.agents[i].name for pos, i in enumerate(routable)}
        dispatch = PromptDispatchExecutor(id="dispatch")
        router = HandoffRouterExecutor(
            id="router", routes=routes, default_route=specialist_ids[0], display_names=display_names
        )
        output = HandoffOutputExecutor(id="final_output", stage_name=finisher_name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_edge(dispatch, triage)
        builder.add_edge(triage, router)
        if finisher_name is None:
            for specialist in specialists:
                builder.add_edge(router, specialist)
                builder.add_edge(specialist, output)
            return builder.build()
        finisher_index = next(
            i for i in range(1, len(scenario.agents)) if scenario.agents[i].name == finisher_name
        )
        finisher = _agent_executor(finisher_index, scenario, config=config)
        finisher_gate = HandoffFinisherGateExecutor(id="finisher_gate")
        for specialist in specialists:
            builder.add_edge(router, specialist)
            builder.add_edge(specialist, finisher_gate)
        builder.add_edge(finisher_gate, finisher)
        builder.add_edge(finisher, output)
        return builder.build()


    def build_group_chat_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        from agent_framework.orchestrations import GroupChatBuilder

        participants = _agents_for(scenario, config=config)

        def round_robin_selector(state: Any) -> str:
            participant_names = list(state.participants.keys())
            return participant_names[state.current_round % len(participant_names)]

        def stop_after_council(messages: list[Any]) -> bool:
            assistant_messages = [m for m in messages if getattr(m, "role", None) == "assistant"]
            if len(assistant_messages) >= 7:
                return True
            last_text = getattr(messages[-1], "text", "").lower() if messages else ""
            return "approved" in last_text and "recommendation" in last_text

        return GroupChatBuilder(
            participants=participants,
            selection_func=round_robin_selector,
            termination_condition=stop_after_council,
            intermediate_output_from=participants,
        ).build()


    def build_magentic_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        from agent_framework.orchestrations import MagenticBuilder

        agents = _agents_for(scenario, config=config)
        manager_agent = agents[0]
        participants = agents[1:]
        return MagenticBuilder(
            participants=participants,
            intermediate_output_from=participants,
            manager_agent=manager_agent,
            max_round_count=10,
            max_stall_count=3,
            max_reset_count=2,
        ).build()


    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        builders = {
            "sequential": build_sequential_workflow,
            "concurrent": build_concurrent_workflow,
            "handoff": build_handoff_workflow,
            "group-chat": build_group_chat_workflow,
            "magentic": build_magentic_workflow,
        }
        return builders[scenario.pattern](scenario, config=config)


    def workflow_result_to_text(result: Any) -> str:
        outputs = result.get_outputs() if hasattr(result, "get_outputs") else result
        intermediate = result.get_intermediate_outputs() if hasattr(result, "get_intermediate_outputs") else []
        if not outputs:
            intermediate_text = join_readable_outputs(intermediate)
            return clean_workflow_text(intermediate_text) or "No workflow output was produced."
        output_text = join_readable_outputs(outputs)
        if intermediate and should_use_intermediate_outputs(output_text):
            intermediate_text = join_readable_outputs(intermediate)
            if intermediate_text:
                return clean_workflow_text(intermediate_text)
        return clean_workflow_text(output_text) or "No readable workflow text was produced."


    def join_readable_outputs(outputs: Any) -> str:
        return "\n\n".join(text for output in outputs if (text := agent_response_to_text(output)))


    def should_use_intermediate_outputs(output_text: str) -> bool:
        normalized = output_text.strip().lower()
        if not normalized:
            return True
        if len(normalized) >= 160:
            return False
        markers = (
            "termination condition",
            "maximum reset count",
            "maximum stall count",
            "workflow terminated",
            "group chat has reached its termination condition",
        )
        return any(marker in normalized for marker in markers)


    def agent_response_to_text(value: Any) -> str:
        text = clean_workflow_text(extract_text(value))
        return text


    def clean_workflow_text(text: str) -> str:
        """Remove leading framework status lines when useful scenario text follows."""

        lines = text.splitlines()
        while lines and is_framework_status_line(lines[0]) and any(line.strip() for line in lines[1:]):
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
        return "\n".join(lines).strip()


    def is_framework_status_line(line: str) -> bool:
        normalized = line.strip().lower()
        return (
            normalized.startswith("invalid next speaker:")
            or normalized.startswith("magentic orchestrator:")
            or normalized.startswith("maximum consecutive function call errors reached")
        )


    def extract_text(value: Any, seen: set[int] | None = None) -> str:
        if value is None:
            return ""
        if seen is None:
            seen = set()
        value_id = id(value)
        if value_id in seen:
            return ""
        seen.add(value_id)
        if isinstance(value, str):
            return "" if is_object_repr(value) else value
        text = getattr(value, "text", None)
        if isinstance(text, str) and text and not is_object_repr(text):
            return text
        messages = getattr(value, "messages", None)
        if messages:
            parts: list[str] = []
            for message in messages:
                author = getattr(message, "author_name", None) or getattr(message, "role", None) or "assistant"
                message_text = extract_text(message, seen)
                if message_text:
                    parts.append(f"[{author}] {message_text}")
            if parts:
                return "\n".join(parts)
        contents = getattr(value, "contents", None)
        if contents:
            return "\n".join(part for content in contents if (part := extract_text(content, seen)))
        items = getattr(value, "items", None)
        if items and not callable(items):
            return "\n".join(part for item in items if (part := extract_text(item, seen)))
        result = getattr(value, "result", None)
        if result is not None:
            return extract_text(result, seen)
        if isinstance(value, Mapping):
            parts = [extract_text(value.get(key), seen) for key in ("text", "content", "message", "summary", "result")]
            return "\n".join(part for part in parts if part)
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            return "\n".join(part for item in value if (part := extract_text(item, seen)))
        fallback = str(value)
        return "" if is_object_repr(fallback) else fallback


    def is_object_repr(value: str) -> bool:
        return value.startswith("<") and " object at 0x" in value and value.endswith(">")


    def group_chat_learning_summary(
        scenario: ScenarioSpec,
        prompt: str,
        framework_text: str,
    ) -> str:
        """Explain a completed group-chat run when this framework build hides the transcript."""

        lines = [
            "Group chat completed.",
            "",
            f"Framework result: {framework_text.strip()}",
            "",
            "Learning view:",
            "- The workflow used Microsoft Agent Framework's GroupChatBuilder with LLM-backed participants.",
            "- Selection is code-defined round robin; termination is code-defined from assistant messages.",
            f"- The submitted scenario prompt was: {prompt}",
            "- Participant order:",
        ]
        for index, spec in enumerate(scenario.agents, start=1):
            tools = ", ".join(spec.mcp_tools) if spec.mcp_tools else "no domain tools"
            lines.append(f"  {index}. {spec.name}: {spec.description} ({tools})")
        tool_names = sorted({tool for spec in scenario.agents for tool in spec.mcp_tools})
        if tool_names:
            lines.append("- Grounding sources available to tool-enabled agents:")
            for tool_name in tool_names:
                lines.append(f"  - {tool_name}")
        lines.extend(
            [
                "",
                "Note: this local Agent Framework build returned the group-chat termination marker",
                "without exposing participant turns through get_intermediate_outputs(). The notebook",
                "keeps the framework run intact and prints this learning summary so the scenario",
                "still explains the orchestration shape and agent responsibilities.",
            ]
        )
        return "\n".join(lines)
    '''


def diagram_cell(project: dict[str, str], is_quote_to_cash: bool) -> str:
    api_boundary = project["api_boundary"]
    input_label = project["input_label"]
    output_label = project["output_label"]
    quote_call = "\n    quote_to_cash_diagram = display_quote_to_cash_flow(SCENARIO)" if is_quote_to_cash else ""
    return f'''
    import base64
    import html
    from dataclasses import dataclass

    from IPython.display import HTML, display


    @dataclass(frozen=True)
    class ScenarioFlowDiagram:
        title: str
        mermaid: str
        image_url: str


    def scenario_flow_diagram(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        mermaid = _diagram_source(scenario, api_boundary="{api_boundary}", input_label="{input_label}")
        return ScenarioFlowDiagram(
            title=f"{{scenario.title}} Flow",
            mermaid=mermaid,
            image_url=_mermaid_image_url(mermaid),
        )


    def display_scenario_flow(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        diagram = scenario_flow_diagram(scenario)
        display(
            HTML(
                '<figure style="margin: 0">'
                f'<img src="{{html.escape(diagram.image_url)}}" alt="{{html.escape(diagram.title)}}" '
                'style="max-width: 100%; height: auto;" />'
                f'<figcaption style="font-size: 0.9em; color: #555;">{{html.escape(diagram.title)}}</figcaption>'
                "</figure>"
            )
        )
        return diagram


    def _diagram_source(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        if scenario.pattern == "sequential":
            return _sequential_diagram(scenario, api_boundary=api_boundary, input_label=input_label)
        if scenario.pattern == "concurrent":
            return _concurrent_diagram(scenario, api_boundary=api_boundary, input_label=input_label)
        if scenario.pattern == "handoff":
            return _handoff_diagram(scenario, api_boundary=api_boundary, input_label=input_label)
        if scenario.pattern == "group-chat":
            return _group_chat_diagram(scenario, api_boundary=api_boundary, input_label=input_label)
        if scenario.pattern == "magentic":
            return _magentic_diagram(scenario, api_boundary=api_boundary, input_label=input_label)
        raise ValueError(f"Unsupported pattern '{{scenario.pattern}}'.")


    def _sequential_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        previous = "orchestrator"
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(scenario.agents, start=1):
            node = f"agent{{index}}"
            lines.append(f"    {{previous}} -->|stage {{index}}| {{node}}[{{_label(agent.name)}}]")
            previous = node
            pairs.append((agent, node))
        lines.append(f"    {{previous}} --> output[{output_label}]")
        lines.extend(_mcp_tool_links(pairs))
        return "\\n".join(lines)


    def _concurrent_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        synthesizer = next(
            (agent for agent in scenario.agents if agent.name == scenario.concurrent_synthesizer), None
        )
        parallel = [agent for agent in scenario.agents if agent is not synthesizer]
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append("    orchestrator --> fanout{{Fan out same request}}")
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(parallel, start=1):
            node = f"agent{{index}}"
            lines.append(f"    fanout --> {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> aggregate{{{{Aggregate findings}}}}")
            pairs.append((agent, node))
        if synthesizer is None:
            lines.append("    aggregate --> output[{output_label}]")
        else:
            lines.append(f"    aggregate --> synthesizer[{{_label(synthesizer.name)}}]")
            lines.append("    synthesizer --> output[{output_label}]")
            pairs.append((synthesizer, "synthesizer"))
        lines.extend(_mcp_tool_links(pairs))
        return "\\n".join(lines)


    def _handoff_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        triage, *others = scenario.agents
        finisher = next((agent for agent in others if agent.name == scenario.handoff_finisher), None)
        specialists = [agent for agent in others if agent is not finisher]
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append(f"    orchestrator --> triage[{{_label(triage.name)}}]")
        lines.append("    triage --> decision{{Ownership decision}}")
        pairs: list[tuple[AgentSpec, str]] = [(triage, "triage")]
        sink = "output[{output_label}]"
        if finisher is not None:
            lines.append(f"    finisher[{{_label(finisher.name)}}] --> output[{output_label}]")
            pairs.append((finisher, "finisher"))
            sink = "finisher"
        for index, agent in enumerate(specialists, start=1):
            node = f"specialist{{index}}"
            lines.append(f"    decision -->|handoff| {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> {{sink}}")
            pairs.append((agent, node))
        lines.extend(_mcp_tool_links(pairs))
        return "\\n".join(lines)


    def _group_chat_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append("    orchestrator --> selector{{Round-robin selector}}")
        previous = "selector"
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(scenario.agents, start=1):
            node = f"agent{{index}}"
            lines.append(f"    {{previous}} --> {{node}}[{{_label(agent.name)}}]")
            previous = node
            pairs.append((agent, node))
        lines.append(f"    {{previous}} --> stop{{{{Termination condition}}}}")
        lines.append("    stop -->|continue| selector")
        lines.append("    stop -->|done| output[{output_label}]")
        lines.extend(_mcp_tool_links(pairs))
        return "\\n".join(lines)


    def _magentic_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        manager, *specialists = scenario.agents
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append(f"    orchestrator --> manager[{{_label(manager.name)}}]")
        lines.append("    manager --> plan{{Plan and delegate}}")
        pairs: list[tuple[AgentSpec, str]] = [(manager, "manager")]
        for index, agent in enumerate(specialists, start=1):
            node = f"specialist{{index}}"
            lines.append(f"    plan --> {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> progress{{{{Progress ledger}}}}")
            pairs.append((agent, node))
        lines.append("    progress -->|replan| manager")
        lines.append("    progress -->|complete or stop| output[{output_label}]")
        lines.extend(_mcp_tool_links(pairs))
        return "\\n".join(lines)


    def _header(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> list[str]:
        return [
            "flowchart TD",
            f"    client[{{_label(input_label)}}] --> api[{{_label(api_boundary)}}]",
            f"    api --> scenario[{{_label('Scenario: ' + scenario.id)}}]",
            f"    scenario --> orchestrator{{{{{{_label(scenario.pattern + ' orchestration')}}}}}}",
        ]


    def _mcp_tool_links(pairs: list[tuple[AgentSpec, str]]) -> list[str]:
        lines: list[str] = []
        for agent, node_id in pairs:
            for tool in agent.mcp_tools:
                lines.append(f"    {{node_id}} -.->|mcp tool| tool_{{tool}}([{{_label(tool)}}])")
        return lines


    def quote_to_cash_flow_diagram(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        mermaid = _quote_to_cash_source(scenario, api_boundary="{api_boundary}")
        return ScenarioFlowDiagram(
            title=f"{{scenario.title}} Quote-To-Cash Flow",
            mermaid=mermaid,
            image_url=_mermaid_image_url(mermaid),
        )


    def display_quote_to_cash_flow(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        diagram = quote_to_cash_flow_diagram(scenario)
        display(
            HTML(
                '<figure style="margin: 0">'
                f'<img src="{{html.escape(diagram.image_url)}}" alt="{{html.escape(diagram.title)}}" '
                'style="max-width: 100%; height: auto;" />'
                f'<figcaption style="font-size: 0.9em; color: #555;">{{html.escape(diagram.title)}}</figcaption>'
                "</figure>"
            )
        )
        return diagram


    def _quote_to_cash_source(scenario: ScenarioSpec, *, api_boundary: str) -> str:
        names = {{agent.name for agent in scenario.agents}}

        def node(role: str) -> str:
            return role if role in names else next(iter(names))

        lines = [
            "flowchart TD",
            f"    client[{{_label('Quote request begins in CRM')}}] --> api[{{_label(api_boundary)}}]",
            f"    api --> scenario[{{_label('Scenario: ' + scenario.id)}}]",
            f"    scenario --> orchestrator{{{{{{_label(scenario.pattern + ' orchestration')}}}}}}",
            f"    orchestrator --> crm[{{_label('CRM system')}}]",
            f"    crm -->|wave 1| trigger[{{_label(node('QuoteTriggerAgent'))}}]",
            f"    crm -->|wave 1| customer[{{_label(node('CustomerContextAgent'))}}]",
            f"    trigger --> store1[({{_label('Orchestration store: customer context')}})]",
            "    customer --> store1",
            f"    store1 -. {{_label('deallocate wave 1')}} .-> freed1(({{_label('agents released')}}))",
            f"    store1 --> product[{{_label('Product / SKU system')}}]",
            f"    product -->|wave 2| sku[{{_label(node('SkuDiscoveryAgent'))}}]",
            f"    product -->|wave 2| fit[{{_label(node('ProductFitAgent'))}}]",
            f"    sku --> store2[({{_label('Orchestration store: product context')}})]",
            "    fit --> store2",
            f"    store2 -. {{_label('deallocate wave 2')}} .-> freed2(({{_label('agents released')}}))",
            f"    store2 --> pricingsys[{{_label('Pricing / finance / legal system')}}]",
            f"    pricingsys -->|wave 3| pricing[{{_label(node('PricingTermsAgent'))}}]",
            f"    pricing --> generation[{{_label(node('QuoteGenerationAgent'))}}]",
            f"    generation --> quote[/{{_label('Final quote package')}}/]",
        ]
        return "\\n".join(lines)


    def _label(value: str) -> str:
        return value.replace('"', "'")


    def _mermaid_image_url(mermaid: str) -> str:
        encoded = base64.urlsafe_b64encode(mermaid.encode("utf-8")).decode("ascii").rstrip("=")
        return f"https://mermaid.ink/img/{{encoded}}"


    flow_diagram = display_scenario_flow(SCENARIO){quote_call}
    print(flow_diagram.mermaid)
    '''


def live_run_cell() -> str:
    return r'''
    import io
    from contextlib import redirect_stderr, redirect_stdout


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    _framework_logs = io.StringIO()
    with redirect_stdout(_framework_logs), redirect_stderr(_framework_logs):
        result = await workflow.run(SAMPLE_PROMPT)
    framework_logs = _framework_logs.getvalue()
    output_text = workflow_result_to_text(result)
    if SCENARIO.pattern == "group-chat" and should_use_intermediate_outputs(output_text):
        output_text = group_chat_learning_summary(SCENARIO, SAMPLE_PROMPT, output_text)

    if not output_text.strip():
        raise RuntimeError("Workflow completed but produced no readable text.")

    print(output_text)
    '''



def flow_diagram_markdown(project: dict[str, str], scenario: Any) -> str:
    pattern = scenario.pattern
    n = len(scenario.agents)
    if pattern == "sequential":
        shape = "a linear chain of " + str(n) + " stages with a stage-gate executor between each pair"
    elif pattern == "concurrent":
        shape = "a fan-out to " + str(n) + " specialists and a labelled fan-in aggregation"
    elif pattern == "handoff":
        shape = "a triage node routing to one of " + str(n - 1) + " specialists via keyword scoring"
    elif pattern == "group-chat":
        shape = str(n) + " participants in a round-robin loop with a code-defined termination function"
    else:
        shape = "a manager agent delegating to " + str(n - 1) + " specialists with progress-ledger replanning"
    boundary = project["api_boundary"]
    return f"""
    ## Flow Diagram

    The diagram below shows {shape} attached to the {boundary}.
    Solid arrows are orchestration edges. Dashed arrows (`-.->`) are tool calls.
    Domain tool nodes use a stadium shape.
    """


def live_run_markdown(scenario: Any) -> str:
    intro = PATTERN_LIVE_RUN_INTRO[scenario.pattern]
    return f"""
    ## Live Run

    {intro}

    > **Instructor note:** `qwen3:14b` runs with `think: False` by default (extended reasoning off).
    > Set `OLLAMA_THINK=true` before the environment cell to enable chain-of-thought reasoning --
    > useful when debugging unexpected routing decisions or tool call sequences.
    """


def post_run_markdown(scenario: Any) -> str:
    inspect = PATTERN_INSPECT[scenario.pattern]
    return f"""
    ## What to Inspect

    {inspect}
    """


def experiments_markdown(project: dict[str, str], scenario: Any) -> str:
    if project["sample_attr"] == "sample_input":
        payload_line = "`RESPONSES_PAYLOAD['input']`"
    else:
        payload_line = "`INVOCATION_PAYLOAD['task']`, `subject`, `artifacts`, or `constraints`"
    return f"""
    ## Experiments

    - Change {payload_line} and rerun the live cell.
    - Override `OLLAMA_MODEL` or `OLLAMA_HOST` before the environment cell to target a different local Ollama setup.
    - Inspect `agent_capability_map(SCENARIO)` and tighten one agent's instructions to see how orchestration behavior changes.
    - Lower `MAX_TOKENS` for faster runs or raise it when {scenario.pattern} needs more room.
    """


def build_notebook(project: dict[str, str], scenario: Any) -> dict[str, Any]:
    data = scenario_data(scenario, project["sample_attr"])
    server = scenario_mcp_server(scenario)
    cells = [
        md(title_markdown(project, scenario)),
        code(environment_cell()),
        md(concept_markdown(project, scenario)),
    ]
    if server:
        cells.append(md(mcp_markdown(server)))
        cells.append(code(quote_to_cash_tools_cell() if server == "quote_to_cash_context" else enterprise_tools_cell()))
    cells.extend(
        [
            code(agent_factory_cell()),
            code(scenario_cell(project, data)),
            code(workflow_cell()),
            md(flow_diagram_markdown(project, scenario)),
            code(diagram_cell(project, scenario.id.startswith("scenario-16-quote-to-cash"))),
            md(live_run_markdown(scenario)),
            code(live_run_cell()),
            md(post_run_markdown(scenario)),
            md(experiments_markdown(project, scenario)),
        ]
    )
    add_cell_ids(cells, scenario.id)
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    for project in PROJECTS:
        scenarios = load_scenarios(project)
        paths = notebook_paths_by_id(project, scenarios)
        for scenario in scenarios:
            notebook = build_notebook(project, scenario)
            path = paths[scenario.id]
            path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
