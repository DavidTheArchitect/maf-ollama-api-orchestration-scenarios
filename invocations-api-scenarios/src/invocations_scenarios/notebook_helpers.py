from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import DEFAULT_OLLAMA_MAX_TOKENS, DEFAULT_OLLAMA_MODEL
from .models import InvocationRequest
from .scenarios import ScenarioSpec

PATTERN_ANATOMY: dict[str, dict[str, str]] = {
    "sequential": {
        "control_flow": "A structured job moves through fixed processing stages.",
        "coordination": "The builder defines the order. The request selects the scenario.",
        "output_behavior": "The response contract returns one summary plus metadata.",
        "best_when": "Use for CI, webhook, or batch jobs with mandatory steps.",
    },
    "concurrent": {
        "control_flow": "Specialists review the same custom payload independently.",
        "coordination": "The builder fans out work and returns aggregated findings.",
        "output_behavior": "The summary can combine independent reviewer perspectives.",
        "best_when": "Use for independent review dimensions such as security and performance.",
    },
    "handoff": {
        "control_flow": "A triage agent routes the job to specialists through handoff tools.",
        "coordination": "The model chooses among allowed handoff targets.",
        "output_behavior": "The summary may include routing traces and specialist findings.",
        "best_when": "Use for tickets or jobs where the owner depends on context.",
    },
    "group-chat": {
        "control_flow": "Agents discuss the job until the advisory condition is met.",
        "coordination": "A selector function controls participant order.",
        "output_behavior": "Intermediate discussion is folded into the structured response.",
        "best_when": "Use when an internal system needs a decision record.",
    },
    "magentic": {
        "control_flow": "A manager dynamically plans and delegates incident work.",
        "coordination": "The manager selects specialists and replans when needed.",
        "output_behavior": "Specialist outputs are converted into the invocation response summary.",
        "best_when": "Use for non-chat jobs that need dynamic investigation.",
    },
}


def default_ollama_options() -> dict[str, Any]:
    """The sample's real Ollama defaults, sourced from the agent factory."""

    from .agents import build_ollama_config

    config = build_ollama_config()
    return {
        "model": config.model,
        "temperature": config.temperature,
        "num_ctx": config.num_ctx,
        "max_tokens": config.max_tokens,
        "think": config.think,
    }


def scenario_summary(scenario: ScenarioSpec) -> dict[str, str]:
    return {
        "id": scenario.id,
        "title": scenario.title,
        "pattern": scenario.pattern,
        "learning_goal": scenario.learning_goal,
        "when_to_use": scenario.when_to_use,
        "sample_task": scenario.sample_task,
    }


def agent_roster(scenario: ScenarioSpec) -> list[dict[str, str]]:
    return [
        {
            "agent": spec.name,
            "description": spec.description,
            "instructions": spec.instructions,
        }
        for spec in scenario.agents
    ]


def pattern_anatomy(scenario: ScenarioSpec) -> dict[str, str]:
    return PATTERN_ANATOMY[scenario.pattern]


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
    """Apply the Aptos-based notebook theme (graceful fallback if Aptos is absent).

    Returns the injected style markup. In a Jupyter front end this also renders
    the style; outside Jupyter it is a harmless no-op that just returns the text.
    """

    try:
        from IPython.display import HTML, display

        display(HTML(_APTOS_STYLE))
    except ImportError:
        pass
    return _APTOS_STYLE


def agent_capability_map(scenario: ScenarioSpec) -> list[dict[str, Any]]:
    """Map each instruction-led LLM agent to its role and optional domain tools."""

    return [
        {
            "agent": spec.name,
            "description": spec.description,
            "instructions": spec.instructions,
            "mcp_tools": list(spec.mcp_tools),
            "mcp_server": spec.mcp_server if spec.mcp_tools else None,
        }
        for spec in scenario.agents
    ]


def mcp_tool_context(scenario: ScenarioSpec) -> dict[str, Any]:
    """Summarize the local MCP tools each agent in the scenario may call.

    Returns the per-agent allowed-tool lists and the de-duplicated set of tools
    used across the scenario. Scenarios with no MCP tools return empty mappings.
    """

    tools_by_agent = {spec.name: list(spec.mcp_tools) for spec in scenario.agents if spec.mcp_tools}
    all_tools_used = sorted({tool for spec in scenario.agents for tool in spec.mcp_tools})
    return {
        "uses_mcp": bool(all_tools_used),
        "tools_by_agent": tools_by_agent,
        "all_tools_used": all_tools_used,
    }


def load_sample_payload(project_root: Path, scenario: ScenarioSpec) -> dict[str, Any]:
    sample_path = project_root / "samples" / f"{scenario.id}.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


def invocation_reference(scenario: ScenarioSpec, request: InvocationRequest) -> dict[str, Any]:
    return {
        "server_command": (
            f"python -m invocations_scenarios --model {DEFAULT_OLLAMA_MODEL} "
            f"--max-tokens {DEFAULT_OLLAMA_MAX_TOKENS} --port 8089"
        ),
        "endpoint": "http://localhost:8089/invocations",
        "scenario": scenario.id,
        "pattern": request.pattern,
    }
