from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ReviewRequest
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
    return {
        "model": "qwen3:14b",
        "temperature": 0,
        "num_ctx": 4096,
        "max_tokens": 500,
        "think": False,
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


def invocation_reference(scenario: ScenarioSpec, request: ReviewRequest) -> dict[str, Any]:
    return {
        "server_command": "python -m review_bot --model qwen3:14b --max-tokens 500 --port 8089",
        "endpoint": "http://localhost:8089/invocations",
        "scenario": scenario.id,
        "pattern": request.pattern,
    }
