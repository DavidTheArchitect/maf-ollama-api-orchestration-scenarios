"""Scenario 16 quote-to-cash (Concurrent) for the Invocations API sample.

Run directly with::

    python -m review_bot.scenarios.scenario_16_quote_to_cash_concurrent
"""

from __future__ import annotations

from .quote_to_cash_common import SAMPLE_REQUEST, staged_agents
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="scenario-16-quote-to-cash-concurrent",
    pattern="concurrent",
    title="Scenario 16: Quote-To-Cash (Concurrent)",
    learning_goal="Learn how the same quote request can be enriched by specialists in parallel, then aggregated into one quote context, instead of a strictly serial RPA flow.",
    when_to_use="Use Concurrent when several enrichment dimensions are independent and can run at the same time before aggregation.",
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
