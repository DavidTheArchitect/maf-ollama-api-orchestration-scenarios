"""Sequential employee onboarding scenario for the Responses API sample."""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="sequential-employee-onboarding",
    pattern="sequential",
    title="Sequential Employee Onboarding",
    learning_goal="Learn how a Responses API endpoint can hide a fixed enterprise onboarding pipeline behind one conversational request, where each department consumes a concrete artifact from the stage before it.",
    when_to_use="Use Responses plus sequential orchestration when later stages depend on earlier artifacts (role profile, access list, granted access) — if departments only shared the same intake form, concurrent orchestration would fit better.",
    sample_input="Create an onboarding plan for a remote enterprise sales director starting in two weeks with CRM, payroll, security, and enablement dependencies.",
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
            "Using the role profile and start date from the HR stage, list the laptop, identity, email, "
            "CRM, collaboration, and device-management tasks with target dates, and output the proposed "
            "access list for security review.",
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
            "Turns departmental artifacts into a manager-ready launch plan.",
            "Combine the role profile, provisioning tasks, security-approved access plan, and payroll "
            "actions into a concise manager checklist with dates, blockers, and first-week success measures.",
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
