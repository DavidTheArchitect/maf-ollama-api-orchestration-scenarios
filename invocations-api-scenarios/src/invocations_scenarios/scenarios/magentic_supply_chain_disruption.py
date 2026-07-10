"""Magentic supply chain disruption job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-supply-chain-disruption",
    pattern="magentic",
    title="Magentic Supply Chain Disruption Job",
    learning_goal="Learn how an invocation can coordinate an open-ended enterprise disruption job through a manager-led agent team.",
    when_to_use="Use Invocations plus magentic orchestration for operations jobs that need dynamic planning, delegation, and replanning.",
    sample_task=(
        "Coordinate response options for a supply chain disruption: the sole supplier of a control "
        "module halted shipments after a factory fire, threatening two product lines. Constraints: "
        "the expedite budget is capped at 250k USD and two strategic customers carry contractual "
        "delivery penalties."
    ),
    agents=(
        AgentSpec("SupplyChainManagerAgent", "Plans and coordinates the disruption response.", "Build the investigation plan, delegate to specialists, reconcile findings, and produce an executive response plan."),
        AgentSpec(
            "SupplierRiskAgent",
            "Assesses supplier status and alternatives.",
            "Investigate supplier constraints, replacement suppliers, qualification risk, and "
            "contractual leverage. Report which options are realistic inside the response window and "
            "what each costs against the expedite budget.",
        ),
        AgentSpec(
            "InventoryPlanningAgent",
            "Assesses stock and allocation.",
            "Analyze inventory exposure, allocation tradeoffs, regional stock, and demand coverage "
            "windows for the two threatened product lines. Report how many weeks each line survives "
            "under current allocation and the best reallocation option.",
        ),
        AgentSpec(
            "ManufacturingOpsAgent",
            "Assesses production impact.",
            "Analyze production sequencing, line changeovers, capacity constraints, and mitigation "
            "options. Report what production can absorb, at what changeover cost, and the earliest "
            "realistic recovery date.",
        ),
        AgentSpec(
            "CustomerCommitmentsAgent",
            "Assesses customer impact.",
            "Identify the affected customer commitments -- especially the two with contractual "
            "delivery penalties -- prioritization options, and communication needs. Report which "
            "commitments to protect first and why.",
        ),
        AgentSpec(
            "FinanceForecastAgent",
            "Assesses financial impact.",
            "Estimate forecast exposure, expedite cost against the 250k USD cap, penalty exposure, "
            "margin impact, and decision points. Report the cheapest option that avoids both "
            "penalties, if one exists.",
        ),
    ),
)


async def run_sample(**config_overrides) -> str:
    """Run this scenario in-process (shared helper in ``scenarios/_runner.py``)."""

    from ._runner import run_sample as _run_sample

    return await _run_sample(SCENARIO, **config_overrides)


if __name__ == "__main__":
    from ._runner import main

    main(SCENARIO)
