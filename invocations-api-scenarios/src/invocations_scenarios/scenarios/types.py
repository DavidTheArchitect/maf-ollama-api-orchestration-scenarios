from __future__ import annotations

from dataclasses import dataclass

from typing import Literal

from ..agents import AgentSpec

PatternName = Literal["sequential", "concurrent", "handoff", "group-chat", "magentic"]


def recommended_max_tokens(scenario_id: str, pattern: PatternName) -> int:
    """Recommended per-agent local token budget for a scenario."""

    if pattern in {"group-chat", "magentic"}:
        return 1500
    if scenario_id.startswith("scenario-16-") or scenario_id == "scenario-18-agent-framework-primitives":
        return 1500
    return 1000


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    pattern: PatternName
    title: str
    learning_goal: str
    when_to_use: str
    sample_task: str
    agents: tuple[AgentSpec, ...]
    #: Recommended per-agent local generation budget for this scenario. Leave
    #: unset to derive 1000 or 1500 from the pattern and scenario family.
    max_tokens: int | None = None
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

    def __post_init__(self) -> None:
        max_tokens = self.max_tokens if self.max_tokens is not None else recommended_max_tokens(self.id, self.pattern)
        if max_tokens not in {1000, 1500}:
            raise ValueError(f"{self.id} max_tokens must be 1000 or 1500, got {max_tokens}.")
        object.__setattr__(self, "max_tokens", max_tokens)
