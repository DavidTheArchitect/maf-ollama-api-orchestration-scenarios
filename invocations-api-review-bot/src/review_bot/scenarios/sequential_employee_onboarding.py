"""Sequential employee onboarding job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-employee-onboarding",
    pattern="sequential",
    title="Sequential Employee Onboarding Job",
    learning_goal="Learn how an invocation can move a structured onboarding job through required enterprise departments.",
    when_to_use="Use Invocations plus sequential orchestration for HRIS, ticketing, or workflow jobs where every request must pass required stages.",
    sample_task="Build an onboarding execution plan for a new enterprise employee.",
    agents=(
        AgentSpec("HrCoordinatorAgent", "Frames the onboarding job.", "Create the onboarding timeline, owner map, and required employee milestones before downstream departments act."),
        AgentSpec("ItProvisioningAgent", "Plans account and device setup.", "Identify identity, laptop, email, CRM, collaboration, and device-management tasks."),
        AgentSpec("SecurityComplianceAgent", "Checks access and compliance requirements.", "Review least-privilege access, mandatory training, data handling, and audit evidence requirements."),
        AgentSpec("PayrollBenefitsAgent", "Plans payroll and benefits setup.", "Add payroll, benefits, tax, direct deposit, and regional compliance actions."),
        AgentSpec("EnablementManagerAgent", "Produces the final execution plan.", "Combine prior outputs into a concise checklist with dates, blockers, and first-week success measures."),
    ),
)
