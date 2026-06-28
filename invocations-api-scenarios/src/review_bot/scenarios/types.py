from __future__ import annotations

from dataclasses import dataclass

from ..agents import AgentSpec


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    pattern: str
    title: str
    learning_goal: str
    when_to_use: str
    sample_task: str
    agents: tuple[AgentSpec, ...]
