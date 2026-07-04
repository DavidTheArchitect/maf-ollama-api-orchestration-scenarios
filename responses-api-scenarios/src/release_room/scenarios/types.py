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
    #: Handoff-only: name of the agent that always runs after the routed
    #: specialist to finish the work (for example the quote or comms owner).
    #: ``None`` keeps the single-hop triage -> router -> specialist shape.
    handoff_finisher: str | None = None
