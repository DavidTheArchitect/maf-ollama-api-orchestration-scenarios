"""Scenario 16 quote-to-cash (Sequential) for the Invocations API sample.

Run directly with::

    python -m review_bot.scenarios.scenario_16_quote_to_cash_sequential
"""

from __future__ import annotations

from .quote_to_cash_common import SAMPLE_REQUEST, staged_agents
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-sequential",
    pattern="sequential",
    title="Scenario 16: Quote-To-Cash (Sequential)",
    learning_goal="Learn the closest agentic version of the staged quote-to-cash pipeline: CRM context, then product context, then pricing/legal, then the quote package. Each stage hands its result to the next.",
    when_to_use="Use Sequential when every quote must pass through the same ordered stages and each stage depends on the previous one's output.",
    sample_task=SAMPLE_REQUEST,
    agents=staged_agents(),
)


async def run_sample(**config_overrides) -> str:
    """Build and run this scenario in-process, returning readable output text."""

    from ..workflows import run_scenario_sample

    return await run_scenario_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(run_sample()))
