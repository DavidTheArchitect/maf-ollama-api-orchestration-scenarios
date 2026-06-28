"""Code-defined function tools shared by the coded agents.

These are plain, deterministic Python callables (no network, no credentials) that
agents invoke as function tools. They are what makes every agent a *coded agent*
rather than a prompt-only agent: the agent's behaviour is shaped by real code it
can call, in addition to any MCP tools.

The Microsoft Agent Framework introspects each callable's signature and docstring
to expose it to the model, so every tool below is fully type-annotated with a
clear docstring. ``CODE_TOOLS`` maps the names referenced by ``AgentSpec.code_tools``
to the callables; ``resolve_code_tools`` turns those names into callables at
agent-construction time.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

_RISK_TIERS: tuple[tuple[int, str], ...] = ((20, "critical"), (12, "high"), (6, "medium"), (0, "low"))


def note_observation(category: str, observation: str) -> str:
    """Record a single structured observation.

    Args:
        category: Short label for the kind of observation (e.g. "risk", "scope").
        observation: The observation text.

    Returns:
        A normalized ``[category] observation`` line.
    """

    return f"[{category.strip().lower()}] {observation.strip()}"


def rate_risk(impact: int, likelihood: int) -> dict[str, object]:
    """Score a risk deterministically from impact and likelihood.

    Args:
        impact: Impact on a 1-5 scale (values are clamped).
        likelihood: Likelihood on a 1-5 scale (values are clamped).

    Returns:
        A mapping with the clamped inputs, the product ``score`` (1-25), and a
        named ``tier``.
    """

    impact_v = max(1, min(5, int(impact)))
    likelihood_v = max(1, min(5, int(likelihood)))
    score = impact_v * likelihood_v
    tier = next(name for floor, name in _RISK_TIERS if score >= floor)
    return {"impact": impact_v, "likelihood": likelihood_v, "score": score, "tier": tier}


def make_checklist(items: Sequence[str]) -> str:
    """Render a Markdown checklist from a list of items."""

    cleaned = [item.strip() for item in items if str(item).strip()]
    if not cleaned:
        return "- [ ] (no items)"
    return "\n".join(f"- [ ] {item}" for item in cleaned)


def extract_action_items(text: str) -> list[str]:
    """Extract concise action items from free text.

    Splits on newlines and sentence boundaries, keeps imperative-looking, short
    lines, and de-duplicates while preserving order.
    """

    raw: list[str] = []
    for line in (text or "").replace(";", "\n").splitlines():
        for piece in line.split(". "):
            candidate = piece.strip(" -*\t.").strip()
            if 0 < len(candidate) <= 160:
                raw.append(candidate)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in raw:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(item)
    return ordered[:8]


def tally_votes(votes: Sequence[str]) -> dict[str, object]:
    """Tally approve/reject/abstain style votes deterministically.

    Any vote text containing "approve"/"yes" counts as approve, "reject"/"no"/
    "block" as reject, otherwise abstain. Returns counts and the decision.
    """

    counts = {"approve": 0, "reject": 0, "abstain": 0}
    for vote in votes:
        text = str(vote).lower()
        if any(token in text for token in ("reject", "no-go", "block", "deny", "veto")):
            counts["reject"] += 1
        elif any(token in text for token in ("approve", "yes", "go ahead", "go-ahead")):
            counts["approve"] += 1
        else:
            counts["abstain"] += 1
    if counts["approve"] > counts["reject"]:
        decision = "approved"
    elif counts["reject"] > counts["approve"]:
        decision = "rejected"
    else:
        decision = "undecided"
    return {"counts": counts, "decision": decision}


def compose_summary(sections: dict[str, str]) -> str:
    """Compose a readable summary from a mapping of heading -> content."""

    if not sections:
        return "No content to summarize."
    return "\n\n".join(f"## {heading}\n{content.strip()}" for heading, content in sections.items())


CODE_TOOLS: dict[str, Callable[..., object]] = {
    "note_observation": note_observation,
    "rate_risk": rate_risk,
    "make_checklist": make_checklist,
    "extract_action_items": extract_action_items,
    "tally_votes": tally_votes,
    "compose_summary": compose_summary,
}


#: Role keyword -> default code tools. Every agent is a coded agent: if a scenario
#: does not set ``code_tools`` explicitly, the role name/description selects a
#: sensible deterministic default here, so no agent is ever prompt-only.
_ROLE_TOOL_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("risk", "fraud", "security", "threat", "priority", "incident"), ("note_observation", "rate_risk")),
    (("board", "chair", "council", "panel", "vote", "debate"), ("note_observation", "tally_votes")),
    (("plan", "manager", "trigger", "intake", "coordinat", "orchestrat", "scope"), ("note_observation", "make_checklist")),
    (("summary", "editor", "writer", "docs", "comms", "generation", "packet", "report", "action", "quote"), ("compose_summary", "extract_action_items")),
    (("validate", "fit", "check", "audit", "review", "evidence", "compat", "depend"), ("note_observation", "make_checklist")),
)


def default_code_tools_for(name: str, description: str = "") -> tuple[str, ...]:
    """Pick deterministic default code tools for an agent role."""

    text = f"{name} {description}".lower()
    for keywords, tools in _ROLE_TOOL_RULES:
        if any(keyword in text for keyword in keywords):
            return tools
    return ("note_observation", "compose_summary")


def effective_code_tools(spec: object) -> tuple[str, ...]:
    """Return the code tools an agent will actually receive.

    Uses the scenario's explicit ``code_tools`` when present, otherwise the
    role-based default. The result is always non-empty, so every agent is coded.
    """

    explicit = tuple(getattr(spec, "code_tools", ()) or ())
    if explicit:
        return explicit
    return default_code_tools_for(getattr(spec, "name", ""), getattr(spec, "description", ""))


def resolve_code_tools(names: Sequence[str]) -> list[Callable[..., object]]:
    """Resolve code-tool names to callables, raising on unknown names."""

    resolved: list[Callable[..., object]] = []
    for name in names:
        try:
            resolved.append(CODE_TOOLS[name])
        except KeyError as exc:
            raise ValueError(
                f"Unknown code tool '{name}'. Expected one of: {', '.join(sorted(CODE_TOOLS))}"
            ) from exc
    return resolved


AVAILABLE_CODE_TOOLS: tuple[str, ...] = tuple(sorted(CODE_TOOLS))
