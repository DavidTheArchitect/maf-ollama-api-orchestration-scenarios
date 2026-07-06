"""Sequential employee onboarding job scenario for the Invocations API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-employee-onboarding",
    pattern="sequential",
    title="Sequential Employee Onboarding Job",
    learning_goal="Learn how an invocation can move a structured onboarding job through required enterprise departments, where each stage consumes a concrete artifact from the stage before it.",
    when_to_use="Use Invocations plus sequential orchestration for HRIS, ticketing, or workflow jobs where later stages depend on earlier artifacts — if departments only shared the same intake payload, concurrent orchestration would fit better.",
    sample_task="Build an onboarding execution plan for a new enterprise employee.",
    agents=(
        AgentSpec(
            "HrCoordinatorAgent",
            "Produces the role profile every downstream stage consumes.",
            "Create the onboarding timeline and a concrete role profile: role, level, department, manager, "
            "start date, location, and employment type. Downstream departments provision against this "
            "profile, so state it explicitly.",
        ),
        AgentSpec(
            "ItProvisioningAgent",
            "Provisions against HR's role profile.",
            "Using the role profile and start date from the HR stage, list identity, laptop, email, CRM, "
            "collaboration, and device-management tasks with target dates, and output the proposed access "
            "list for security review.",
        ),
        AgentSpec(
            "SecurityComplianceAgent",
            "Reviews IT's proposed access list.",
            "Review the access list the IT stage proposed against least-privilege for the stated role. "
            "Approve, trim, or flag each item, and add mandatory training, data handling, and audit "
            "evidence requirements.",
        ),
        AgentSpec(
            "PayrollBenefitsAgent",
            "Sets up payroll from the role profile and approved plan.",
            "Using the role profile's location, employment type, and start date, add payroll, benefits, "
            "tax, direct deposit, and regional compliance actions consistent with the approved access plan.",
        ),
        AgentSpec(
            "EnablementManagerAgent",
            "Turns departmental artifacts into the final execution plan.",
            "Combine the role profile, provisioning tasks, security-approved access plan, and payroll "
            "actions into a concise checklist with dates, blockers, and first-week success measures.",
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
