"""Scenario 16 quote-to-cash (Handoff) for the Responses API sample.

Run directly with::

    python -m release_room.scenarios.scenario_16_quote_to_cash_handoff
"""

from __future__ import annotations

from .quote_to_cash_common import SAMPLE_REQUEST, staged_agents
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-handoff",
    pattern="handoff",
    title="Scenario 16: Quote-To-Cash (Handoff)",
    learning_goal="Learn dynamic routing where a trigger/customer-context agent hands the quote off to product, pricing, legal, and quote-generation specialists based on what the request actually needs.",
    when_to_use="Use Handoff when the next specialist depends on context and the model should choose the route within an allowed handoff graph.",
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
