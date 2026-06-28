"""Sequential employee onboarding scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-employee-onboarding",
    pattern="sequential",
    title="Sequential Employee Onboarding",
    learning_goal="Learn how a Responses API endpoint can hide a fixed enterprise onboarding pipeline behind one conversational request.",
    when_to_use="Use Responses plus sequential orchestration when a user asks for a complete plan that must pass through required enterprise departments.",
    sample_input="Create an onboarding plan for a remote enterprise sales director starting in two weeks with CRM, payroll, security, and enablement dependencies.",
    agents=(
        AgentSpec("HrCoordinatorAgent", "Frames the onboarding journey and required employee milestones.", "Create the onboarding timeline, owner map, and employee-facing milestones before handing off to downstream departments."),
        AgentSpec("ItProvisioningAgent", "Plans accounts, hardware, and application access.", "Identify laptop, identity, email, CRM, collaboration, and device-management tasks required for the new hire."),
        AgentSpec("SecurityComplianceAgent", "Checks access risk and policy training.", "Review least-privilege access, mandatory training, data handling, and audit evidence requirements."),
        AgentSpec("PayrollBenefitsAgent", "Plans payroll, tax, and benefits setup.", "Add payroll, benefits, tax, direct deposit, and regional compliance actions."),
        AgentSpec("EnablementManagerAgent", "Turns departmental work into a manager-ready launch plan.", "Combine prior outputs into a concise manager checklist with dates, blockers, and first-week success measures."),
    ),
)
