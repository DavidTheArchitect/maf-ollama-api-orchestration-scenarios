"""Scenario 16 quote-to-cash (Group Chat) for the Responses API sample.

Run directly with::

    python -m release_room.scenarios.scenario_16_quote_to_cash_group_chat
"""

from __future__ import annotations

from .quote_to_cash_common import SAMPLE_REQUEST, staged_agents
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-group-chat",
    pattern="group-chat",
    title="Scenario 16: Quote-To-Cash (Group Chat)",
    learning_goal="Learn collaborative quote review where agents debate product fit, pricing risk, legal terms, and final quote readiness until they converge.",
    when_to_use="Use Group Chat when a visible debate and cross-check between roles improves the quote before it is finalized.",
    sample_input=SAMPLE_REQUEST,
    agents=staged_agents(),
)


async def run_sample(**config_overrides) -> str:
    """Build and run this scenario in-process, returning readable output text."""

    from ..workflows import run_scenario_sample

    return await run_scenario_sample(SCENARIO.id, **config_overrides)


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(run_sample()))
