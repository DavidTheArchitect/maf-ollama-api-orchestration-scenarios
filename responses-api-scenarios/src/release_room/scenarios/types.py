from __future__ import annotations

from dataclasses import dataclass

from ..agents import AgentSpec

PatternName = str


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    pattern: PatternName
    title: str
    learning_goal: str
    when_to_use: str
    sample_input: str
    agents: tuple[AgentSpec, ...]
