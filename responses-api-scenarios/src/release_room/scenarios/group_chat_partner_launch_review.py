"""Scenario 17: group chat over the A2A protocol for the Responses API sample.

Two council seats are remote peer agents owned by partner organizations and
reached over the A2A (Agent2Agent) protocol; the orchestration code is the
same group chat used by every other group-chat scenario. Serve the partners
locally with::

    python -m release_room.a2a_servers.partner_agents --port 8765

Run the scenario directly with::

    python -m release_room.scenarios.group_chat_partner_launch_review
"""

from __future__ import annotations

from ..agents import AgentSpec
from .types import ScenarioSpec

SCENARIO = ScenarioSpec(
    id="group-chat-partner-launch-review",
    pattern="group-chat",
    title="Group Chat Partner Launch Review (A2A)",
    learning_goal="Learn how remote peer agents owned by partner organizations join a group chat over the A2A protocol -- the orchestration is unchanged; only where two of the participants live changes.",
    when_to_use="Use group chat over A2A when a decision needs seats from other organizations whose agents, models, and facts you do not host.",
    sample_input=(
        "Decide whether the co-sold analytics integration launches in the 2026-07-15 to 2026-07-31 "
        "window. Partner-side integration status and external compliance status are owned by partner "
        "organizations -- their agents must speak for those facts."
    ),
    termination_phrases=("final recommendation",),
    agents=(
        AgentSpec(
            "ProductLeadAgent",
            "Argues product readiness and launch scope.",
            "Argue product readiness for the co-sold analytics integration: scope clarity, launch goals, "
            "and customer commitments inside the stated window.",
        ),
        AgentSpec(
            "OperationsLeadAgent",
            "Argues support and operational readiness.",
            "Argue operational readiness: support coverage, rollback, monitoring, and incident ownership "
            "across two organizations.",
        ),
        AgentSpec(
            "PartnerSolutionsAgent",
            "ISV partner seat, reached over A2A.",
            "Remote partner agent: its instructions and facts live with the partner organization and are "
            "served behind its A2A agent card.",
            a2a_url="/partner-solutions",
        ),
        AgentSpec(
            "ExternalComplianceAgent",
            "External audit firm seat, reached over A2A.",
            "Remote audit-firm agent: its instructions and facts live with the audit firm and are served "
            "behind its A2A agent card.",
            a2a_url="/compliance",
        ),
        AgentSpec(
            "JointLaunchChairAgent",
            "Synthesizes the joint council and closes each round.",
            "Synthesize the local and partner positions each round, calling out conflicts between the "
            "launch window and partner-side facts. When the council has converged, end your turn with a "
            "line 'FINAL RECOMMENDATION: <launch or hold> - <one-sentence rationale>'.",
        ),
    ),
)


async def run_sample(**config_overrides) -> str:
    """Build and run this scenario in-process, returning readable output text.

    Starts the bundled deterministic partner A2A server on an ephemeral port
    for the duration of the run, so no second terminal is needed.
    """

    import os

    from ..a2a_servers.partner_agents import PartnerA2AServer
    from ..workflows import run_scenario_sample

    with PartnerA2AServer() as server:
        previous = os.environ.get("A2A_PARTNER_BASE_URL")
        os.environ["A2A_PARTNER_BASE_URL"] = server.base_url
        try:
            return await run_scenario_sample(SCENARIO.id, **config_overrides)
        finally:
            if previous is None:
                os.environ.pop("A2A_PARTNER_BASE_URL", None)
            else:
                os.environ["A2A_PARTNER_BASE_URL"] = previous


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(run_sample()))
