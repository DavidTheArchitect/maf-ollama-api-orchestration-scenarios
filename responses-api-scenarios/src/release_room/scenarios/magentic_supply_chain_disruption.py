"""Magentic supply chain disruption scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="magentic-supply-chain-disruption",
    pattern="magentic",
    title="Magentic Supply Chain Disruption",
    learning_goal="Learn how a Responses API endpoint can use a manager-led agent team for open-ended enterprise disruption response.",
    when_to_use="Use Responses plus magentic orchestration when the request needs dynamic planning, delegation, and replanning across enterprise functions.",
    sample_input=(
        "Coordinate a response to a supplier disruption that threatens two product lines, regional "
        "inventory, customer delivery dates, and finance forecasts. Constraints: the expedite budget "
        "is capped at 250k USD and two strategic customers carry contractual delivery penalties."
    ),
    agents=(
        AgentSpec("SupplyChainManagerAgent", "Plans and coordinates the disruption response.", "Build the investigation plan, delegate to specialists, reconcile findings, and produce an executive response plan."),
        AgentSpec("SupplierRiskAgent", "Assesses supplier status and alternatives.", "Investigate supplier constraints, replacement suppliers, qualification risk, and contractual leverage."),
        AgentSpec("InventoryPlanningAgent", "Assesses stock, allocation, and demand coverage.", "Analyze inventory exposure, allocation tradeoffs, regional stock, and demand coverage windows."),
        AgentSpec("ManufacturingOpsAgent", "Assesses production and schedule impact.", "Analyze production sequencing, line changeovers, capacity constraints, and mitigation options."),
        AgentSpec("CustomerCommitmentsAgent", "Assesses customer impact and communication.", "Identify affected customer commitments, prioritization options, and communication needs."),
        AgentSpec("FinanceForecastAgent", "Assesses margin, cash, and forecast impact.", "Estimate forecast exposure, expedite cost, margin impact, and financial decision points."),
    ),
)
