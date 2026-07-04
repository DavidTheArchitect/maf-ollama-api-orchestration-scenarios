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
        "Coordinate response options for a supply chain disruption threatening two product lines. "
        "Constraints: the expedite budget is capped at 250k USD and two strategic customers carry "
        "contractual delivery penalties."
    ),
    agents=(
        AgentSpec("SupplyChainManagerAgent", "Plans and coordinates the disruption response.", "Build the investigation plan, delegate to specialists, reconcile findings, and produce an executive response plan."),
        AgentSpec("SupplierRiskAgent", "Assesses supplier status and alternatives.", "Investigate supplier constraints, replacement suppliers, qualification risk, and contractual leverage."),
        AgentSpec("InventoryPlanningAgent", "Assesses stock and allocation.", "Analyze inventory exposure, allocation tradeoffs, regional stock, and demand coverage windows."),
        AgentSpec("ManufacturingOpsAgent", "Assesses production impact.", "Analyze production sequencing, line changeovers, capacity constraints, and mitigation options."),
        AgentSpec("CustomerCommitmentsAgent", "Assesses customer impact.", "Identify affected customer commitments, prioritization options, and communication needs."),
        AgentSpec("FinanceForecastAgent", "Assesses financial impact.", "Estimate forecast exposure, expedite cost, margin impact, and decision points."),
    ),
)
