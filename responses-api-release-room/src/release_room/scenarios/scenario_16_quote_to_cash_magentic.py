"""Scenario 16 quote-to-cash (Magentic) for the Responses API sample.

Run directly with::

    python -m release_room.scenarios.scenario_16_quote_to_cash_magentic
"""

from __future__ import annotations

from .quote_to_cash_common import SAMPLE_REQUEST, manager_first_agents
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-magentic",
    pattern="magentic",
    title="Scenario 16: Quote-To-Cash (Magentic)",
    learning_goal="Learn manager-led planning where a quote manager dynamically delegates to trigger, customer, SKU, fit, and pricing specialists and replans until the quote package is ready.",
    when_to_use="Use Magentic for open-ended quote assembly where a manager must plan, delegate, and replan as new context arrives.",
    sample_input=SAMPLE_REQUEST,
    agents=manager_first_agents(),
)


async def run_sample(**config_overrides) -> str:
    """Build and run this scenario in-process, returning readable output text."""

    from ..workflows import run_scenario_sample

    return await run_scenario_sample(SCENARIO.id, **config_overrides)


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(run_sample()))
