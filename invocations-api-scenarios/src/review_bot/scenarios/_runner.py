"""Shared run-sample helpers so every scenario module is directly runnable.

Each scenario module keeps the same three-line tail (an async ``run_sample``
plus a ``__main__`` hook) instead of its own copy of the boilerplate.
"""

from __future__ import annotations

from typing import Any

from .types import ScenarioSpec


async def run_sample(scenario: ScenarioSpec, **config_overrides: Any) -> str:
    """Build and run ``scenario`` in-process and return readable output text."""

    from ..workflows import run_scenario_sample

    return await run_scenario_sample(scenario.id, **config_overrides)


def main(scenario: ScenarioSpec) -> None:
    """CLI entry point: run the scenario sample and print its output."""

    import asyncio

    print(asyncio.run(run_sample(scenario)))
