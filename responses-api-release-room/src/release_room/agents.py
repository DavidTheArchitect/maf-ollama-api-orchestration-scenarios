from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    instructions: str


def create_copilot_agent(spec: AgentSpec, *, model: str | None = None) -> Any:
    """Create a GitHub Copilot-backed MAF agent.

    The GitHub Copilot integration has moved quickly. This helper supports the
    direct constructor shape documented in newer examples and the older
    default_options shape used in early samples.
    """

    from agent_framework.github import GitHubCopilotAgent

    model = model or os.getenv("GITHUB_COPILOT_MODEL") or None
    instructions = f"You are {spec.name}. {spec.instructions}"

    attempts: list[dict[str, Any]] = [
        {
            "name": spec.name,
            "description": spec.description,
            "instructions": instructions,
        },
        {
            "name": spec.name,
            "description": spec.description,
            "default_options": {"instructions": instructions},
        },
        {
            "default_options": {"instructions": instructions},
        },
    ]

    if model:
        attempts[0]["model"] = model
        attempts[1]["default_options"]["model"] = model
        attempts[2]["default_options"]["model"] = model

    last_error: TypeError | None = None
    for kwargs in attempts:
        try:
            return GitHubCopilotAgent(**kwargs)
        except TypeError as exc:
            last_error = exc

    raise RuntimeError(f"Could not construct GitHubCopilotAgent for {spec.name}") from last_error
