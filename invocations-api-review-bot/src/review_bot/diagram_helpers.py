from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from typing import Any

from .scenarios import ScenarioSpec


@dataclass(frozen=True)
class ScenarioFlowDiagram:
    title: str
    mermaid: str
    image_url: str


def scenario_flow_diagram(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
    mermaid = _diagram_source(scenario, api_boundary="Invocations API /invocations", input_label="Custom job payload")
    return ScenarioFlowDiagram(
        title=f"{scenario.title} Flow",
        mermaid=mermaid,
        image_url=_mermaid_image_url(mermaid),
    )


def display_scenario_flow(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
    diagram = scenario_flow_diagram(scenario)
    try:
        from IPython.display import HTML, display
    except ImportError:
        print(diagram.mermaid)
        return diagram

    display(
        HTML(
            '<figure style="margin: 0">'
            f'<img src="{html.escape(diagram.image_url)}" alt="{html.escape(diagram.title)}" '
            'style="max-width: 100%; height: auto;" />'
            f'<figcaption style="font-size: 0.9em; color: #555;">{html.escape(diagram.title)}</figcaption>'
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
    raise ValueError(f"Unsupported pattern '{scenario.pattern}' for scenario '{scenario.id}'.")


def _sequential_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
    lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
    previous = "orchestrator"
    pairs: list[tuple[Any, str]] = []
    for index, agent in enumerate(scenario.agents, start=1):
        node = f"agent{index}"
        lines.append(f"    {previous} -->|stage {index}| {node}[{_label(agent.name)}]")
        previous = node
        pairs.append((agent, node))
    lines.append(f"    {previous} --> output[Structured invocation response]")
    lines.extend(_mcp_tool_links(pairs))
    return "\n".join(lines)


def _concurrent_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
    lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
    lines.append("    orchestrator --> fanout{{Fan out same payload}}")
    pairs: list[tuple[Any, str]] = []
    for index, agent in enumerate(scenario.agents, start=1):
        node = f"agent{index}"
        lines.append(f"    fanout --> {node}[{_label(agent.name)}]")
        lines.append(f"    {node} --> aggregate{{Aggregate findings}}")
        pairs.append((agent, node))
    lines.append("    aggregate --> output[Structured invocation response]")
    lines.extend(_mcp_tool_links(pairs))
    return "\n".join(lines)


def _handoff_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
    triage, *specialists = scenario.agents
    lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
    lines.append(f"    orchestrator --> triage[{_label(triage.name)}]")
    lines.append("    triage --> decision{Ownership decision}")
    pairs: list[tuple[Any, str]] = [(triage, "triage")]
    for index, agent in enumerate(specialists, start=1):
        node = f"specialist{index}"
        lines.append(f"    decision -->|handoff| {node}[{_label(agent.name)}]")
        lines.append(f"    {node} --> triage")
        pairs.append((agent, node))
    lines.append("    triage --> output[Structured invocation response]")
    lines.extend(_mcp_tool_links(pairs))
    return "\n".join(lines)


def _group_chat_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
    lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
    lines.append("    orchestrator --> selector{Round-robin selector}")
    previous = "selector"
    pairs: list[tuple[Any, str]] = []
    for index, agent in enumerate(scenario.agents, start=1):
        node = f"agent{index}"
        lines.append(f"    {previous} --> {node}[{_label(agent.name)}]")
        previous = node
        pairs.append((agent, node))
    lines.append(f"    {previous} --> stop{{Termination condition}}")
    lines.append("    stop -->|continue| selector")
    lines.append("    stop -->|done| output[Structured invocation response]")
    lines.extend(_mcp_tool_links(pairs))
    return "\n".join(lines)


def _magentic_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
    manager, *specialists = scenario.agents
    lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
    lines.append(f"    orchestrator --> manager[{_label(manager.name)}]")
    lines.append("    manager --> plan{Plan and delegate}")
    pairs: list[tuple[Any, str]] = [(manager, "manager")]
    for index, agent in enumerate(specialists, start=1):
        node = f"specialist{index}"
        lines.append(f"    plan --> {node}[{_label(agent.name)}]")
        lines.append(f"    {node} --> progress{{Progress ledger}}")
        pairs.append((agent, node))
    lines.append("    progress -->|replan| manager")
    lines.append("    progress -->|complete or stop| output[Structured invocation response]")
    lines.extend(_mcp_tool_links(pairs))
    return "\n".join(lines)


def _header(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> list[str]:
    return [
        "flowchart TD",
        f"    client[{_label(input_label)}] --> api[{_label(api_boundary)}]",
        f"    api --> prompt[Build orchestration prompt]",
        f"    prompt --> scenario[{_label('Request-selected scenario: ' + scenario.id)}]",
        f"    scenario --> orchestrator{{{_label(scenario.pattern + ' orchestration')}}}",
    ]


def _mcp_tool_links(pairs: list[tuple[Any, str]]) -> list[str]:
    """Render dashed Mermaid links from MCP-enabled agents to their tools.

    ``pairs`` maps each agent to the diagram node id that represents it. Agents
    without ``mcp_tools`` produce no links, so non-MCP scenarios are unchanged.
    Tool nodes are shared across agents so a tool used by several agents shows up
    once with multiple dashed edges pointing at it.
    """

    if not any(getattr(agent, "mcp_tools", ()) for agent, _ in pairs):
        return []
    lines: list[str] = []
    for agent, node_id in pairs:
        for tool in getattr(agent, "mcp_tools", ()):
            lines.append(f"    {node_id} -.->|mcp tool| tool_{tool}([{_label(tool)}])")
    return lines


def _label(value: str) -> str:
    return value.replace('"', "'")


def _mermaid_image_url(mermaid: str) -> str:
    encoded = base64.urlsafe_b64encode(mermaid.encode("utf-8")).decode("ascii").rstrip("=")
    return f"https://mermaid.ink/img/{encoded}"
