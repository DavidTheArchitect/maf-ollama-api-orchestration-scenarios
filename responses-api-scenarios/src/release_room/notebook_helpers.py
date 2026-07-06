from __future__ import annotations

from typing import Any

from .agents import DEFAULT_OLLAMA_MAX_TOKENS, DEFAULT_OLLAMA_MODEL
from .scenarios import ScenarioSpec

# Re-exported so existing imports (tests, notebooks) keep working after the
# runtime output handling moved to its own module.
from .output_formatting import (  # noqa: F401
    agent_response_to_text,
    clean_workflow_text,
    extract_text,
    is_framework_status_line,
    is_object_repr,
    join_readable_outputs,
    should_use_intermediate_outputs,
    workflow_result_to_text,
)

PATTERN_ANATOMY: dict[str, dict[str, str]] = {
    "sequential": {
        "control_flow": "Agents run in a fixed order, with each step receiving the prior step's response.",
        "coordination": "The builder defines the chain. The model does not decide which agent acts next.",
        "output_behavior": "Final and intermediate agent responses can be inspected to see the pipeline.",
        "best_when": "Use for repeatable pipelines where every request needs the same stages.",
    },
    "concurrent": {
        "control_flow": "All specialist agents receive the same input and run independently.",
        "coordination": "The builder fans out work and aggregates the participant outputs.",
        "output_behavior": "Each participant contributes a separate perspective.",
        "best_when": "Use when independent reviews can happen in parallel.",
    },
    "handoff": {
        "control_flow": "A start agent routes the conversation to specialists through handoff tools.",
        "coordination": "The model chooses handoffs within the allowed handoff graph.",
        "output_behavior": "Outputs may include function-call records plus specialist messages.",
        "best_when": "Use when the right specialist depends on the user's issue.",
    },
    "group-chat": {
        "control_flow": "Agents take turns in a discussion until the termination condition is met.",
        "coordination": "A selector function chooses the next participant.",
        "output_behavior": "The transcript shows critique, refinement, and convergence.",
        "best_when": "Use when visible debate and iteration improve the answer.",
    },
    "magentic": {
        "control_flow": "A manager agent plans work and delegates dynamically to specialists.",
        "coordination": "The manager replans as the task evolves or stalls.",
        "output_behavior": "Specialist outputs show the manager-led investigation path.",
        "best_when": "Use for open-ended work that needs planning and replanning.",
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
        "sample_input": scenario.sample_input,
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


def responses_api_reference(scenario: ScenarioSpec) -> dict[str, Any]:
    return {
        "server_command": (
            f"python -m release_room --scenario {scenario.id} "
            f"--model {DEFAULT_OLLAMA_MODEL} --max-tokens {DEFAULT_OLLAMA_MAX_TOKENS} --port 8088"
        ),
        "endpoint": "http://localhost:8088/responses",
        "payload": {"input": scenario.sample_input, "stream": False},
    }
