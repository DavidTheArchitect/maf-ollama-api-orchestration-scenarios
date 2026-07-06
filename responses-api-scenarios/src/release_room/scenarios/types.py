from __future__ import annotations

from dataclasses import dataclass

from typing import Literal

from ..agents import AgentSpec

PatternName = Literal["sequential", "concurrent", "handoff", "group-chat", "magentic"]


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
    #: Concurrent-only: name of the agent that runs after fan-in to synthesize
    #: the labelled parallel findings into one deliverable. ``None`` keeps the
    #: plain fan-out -> fan-in -> aggregated output shape.
    concurrent_synthesizer: str | None = None
    #: Group-chat-only: phrases that must all appear in the closing message of
    #: a round-robin cycle for the discussion to end early. The last agent in
    #: the roster closes each cycle, so it always gets the final word. Empty
    #: means the chat simply runs its full cycle budget.
    termination_phrases: tuple[str, ...] = ()
