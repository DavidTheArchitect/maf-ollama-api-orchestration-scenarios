from __future__ import annotations

import importlib
import json
import sys
import textwrap
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIMITIVES_SCENARIO_ID = "scenario-18-agent-framework-primitives"

PROJECTS = (
    {
        "folder": "responses-api-scenarios",
        "package": "responses_scenarios",
        "api_name": "Responses API",
        "api_boundary": "Responses API /responses",
        "input_label": "OpenAI-style input",
        "output_label": "Responses output",
        "sample_attr": "sample_input",
        "payload_name": "RESPONSES_PAYLOAD",
    },
    {
        "folder": "invocations-api-scenarios",
        "package": "invocations_scenarios",
        "api_name": "Invocations API",
        "api_boundary": "Invocations API /invocations",
        "input_label": "Job payload",
        "output_label": "Invocation summary",
        "sample_attr": "sample_task",
        "payload_name": "INVOCATION_PAYLOAD",
    },
)


PATTERN_DOCS = {
    "sequential": (
        "Sequential orchestration is a fixed pipeline. Each agent receives the original request plus the "
        "work accumulated so far, so the output should read like a controlled handoff from stage to stage.",
        "Best fit: repeatable workflows where every request needs the same ordered checks."
    ),
    "concurrent": (
        "Concurrent orchestration fans one request out to several specialists. They work independently, "
        "then a code-defined fan-in executor labels and combines their findings. Scenarios with a "
        "designated synthesizer hold that agent out of the fan-out and run it after fan-in, so the agent "
        "that combines the perspectives actually sees them.",
        "Best fit: independent reviews where parallel perspectives are more valuable than turn-taking."
    ),
    "handoff": (
        "Handoff orchestration starts with triage, which names the owning specialist with a ROUTE directive. "
        "A code-defined router validates that choice against the allowed routes (falling back to keyword "
        "scoring), and scenarios with a designated finisher always end with that fixed owner completing the work.",
        "Best fit: support, claims, entitlement, and exception flows where ownership depends on context."
    ),
    "group-chat": (
        "Group chat orchestration creates a visible multi-agent discussion. A selector function chooses the "
        "next participant round-robin, and a per-scenario termination function checks the closing message of "
        "each full cycle, so the synthesizer or chair always speaks last.",
        "Best fit: decisions that benefit from critique, tradeoffs, and a short transcript."
    ),
    "magentic": (
        "Magentic orchestration uses a manager agent to plan, delegate, monitor progress, and replan when "
        "the work stalls. It is intentionally more open-ended than the other patterns.",
        "Best fit: ambiguous work where the system must decide which specialists to involve and in what order."
    ),
}


PATTERN_ANATOMY = {
    "sequential": {
        "control_flow": "Agents run in a fixed order, with each stage receiving the prior stage response.",
        "coordination": "The graph defines the chain. The model does not decide which agent acts next.",
        "output_behavior": "The terminal output includes the stage transcript.",
        "best_when": "Use for repeatable pipelines where every request needs the same stages.",
    },
    "concurrent": {
        "control_flow": "Parallel lanes receive the same input and run independently; an optional synthesizer runs after fan-in.",
        "coordination": "The graph fans out work, aggregates labelled outputs, and can forward them to a synthesis agent.",
        "output_behavior": "Each lane contributes a labelled perspective; a synthesizer combines them when declared.",
        "best_when": "Use when independent reviews can happen in parallel.",
    },
    "handoff": {
        "control_flow": "Triage names a ROUTE, the router validates it, one specialist runs (plus an optional fixed finisher).",
        "coordination": "The router honors the triage ROUTE directive and falls back to keyword scoring.",
        "output_behavior": "The output identifies the route, its source (directive or keywords), and the answers.",
        "best_when": "Use when the right owner depends on the request.",
    },
    "group-chat": {
        "control_flow": "Agents take turns in cycles; the last agent closes each cycle and can end the chat.",
        "coordination": "A selector function rotates speakers; termination is checked only at cycle boundaries.",
        "output_behavior": "The transcript shows critique, refinement, and a closing verdict.",
        "best_when": "Use when visible debate improves the answer.",
    },
    "magentic": {
        "control_flow": "A manager plans work and delegates dynamically to specialists.",
        "coordination": "The manager replans as the task evolves or stalls.",
        "output_behavior": "Specialist outputs show the manager-led investigation path.",
        "best_when": "Use for open-ended work that needs planning and replanning.",
    },
}

PATTERN_LIVE_RUN_INTRO = {
    "sequential": (
        "Each agent output is captured by a `StageGateExecutor` and appended to a growing "
        "transcript. The next agent receives both the original prompt and the accumulated "
        "work so far. The final cell prints the complete stage-by-stage log."
    ),
    "concurrent": (
        "The request fans out to the parallel lanes simultaneously. A fan-in executor waits for "
        "every response and labels each contribution. Without a synthesizer the labelled findings "
        "are the output; with one, a `ConcurrentSynthesisGateExecutor` forwards them to the "
        "synthesis agent, which produces the final deliverable. Execution order inside the "
        "fan-out is non-deterministic."
    ),
    "handoff": (
        "Triage runs first and ends with a `ROUTE: <AgentName>` line. The `HandoffRouterExecutor` "
        "honors that directive when it names an allowed route, otherwise it scores each specialist "
        "keyword list against the triage text. If the scenario declares a finisher, the routed "
        "specialist's notes flow to that fixed agent, which completes the deliverable. The output "
        "shows the route taken and whether it came from the model directive or keyword fallback."
    ),
    "group-chat": (
        "Participants speak in round-robin order, and termination is only checked when the "
        "last agent closes a full cycle -- so the synthesizer always gets the final word. "
        "The chat ends early when the scenario's termination phrases appear in that closing "
        "message, and unconditionally after two full cycles. Intermediate outputs from each "
        "participant are surfaced alongside the final transcript."
    ),
    "magentic": (
        "The manager agent plans, delegates to specialists, and replans if work stalls or "
        "reaches a reset limit. With `max_round_count=10`, `max_stall_count=3`, and "
        "`max_reset_count=2`, there is room to iterate. Allow extra time -- this pattern "
        "runs more LLM calls than the others."
    ),
}


PATTERN_INSPECT = {
    "sequential": (
        "Compare the first stage output to the final editor output. Later stages should "
        "build on prior work, not repeat it -- each `StageGateExecutor` carries the full "
        "transcript forward. If a stage ignores prior context, inspect its instructions "
        "and the gate prompt to see exactly what the agent received."
    ),
    "concurrent": (
        "Check that each labelled lane contribution is non-overlapping. Because lanes "
        "receive the same input and run independently, their findings should be additive, "
        "not redundant. When the scenario declares a synthesizer, confirm its final entry "
        "actually reconciles the labelled findings above it rather than repeating one lane."
    ),
    "handoff": (
        "Verify the route matches the triage intent, and check the route source in the output "
        "header: 'model-directive' means the triage agent's ROUTE line was honored; "
        "'keyword-score' means the router fell back to scoring keywords. Try rewording the "
        "input toward a different specialist domain and rerun -- the route should change. "
        "Inspect `ctx.get_state('route')` and `ctx.get_state('route_source')` in the workflow state."
    ),
    "group-chat": (
        "Read the transcript chronologically. Later turns should respond to earlier critiques "
        "rather than restarting the discussion. Termination is checked only at the end of each "
        "full cycle: the chat stops early when the scenario's termination phrases appear in the "
        "closing agent's message, or after two full cycles -- check which condition fired and why."
    ),
    "magentic": (
        "Follow the specialist outputs to reconstruct the manager delegation path. If the "
        "manager replanned, you will see the same specialist invoked more than once or a "
        "different specialist substituted mid-run. A stall (no progress for max_stall_count "
        "rounds) triggers a reset; a second stall terminates the workflow."
    ),
}



#: Per-scenario teaching spotlights: (what-to-inspect line, experiment line).
#: These point learners at each scenario's engineered wrinkle instead of
#: leaving the guidance pattern-generic.
SCENARIO_SPOTLIGHTS: dict[str, tuple[str, str]] = {
    "sequential-release-readiness": (
        "The request carries a finance-freeze constraint and a rollback requirement -- the final go/no-go should cite both.",
        "Remove the freeze constraint from the payload and compare how the risk stage and the final brief change.",
    ),
    "concurrent-pr-review": (
        "The diff summary names three concrete changes (JWKS caching, keyset pagination, test fixture swaps) -- each reviewer should react to the change in its own lane.",
        "Drop one diff item from the payload and check that only the relevant reviewers change their findings.",
    ),
    "handoff-support-triage": (
        "The input deliberately mixes SSO and invoice-export symptoms -- check which owner the triage ROUTE line names and whether the rationale matches.",
        "Reword the payload toward a pure billing problem and confirm the route (and its source) changes.",
    ),
    "group-chat-launch-council": (
        "Watch for the 'FINAL RECOMMENDATION:' line -- if it appears at a cycle end, semantic termination fired; otherwise the two-cycle cap did.",
        "Weaken one stakeholder's instructions and see whether the council converges in one cycle instead of two.",
    ),
    "magentic-incident-response": (
        "The timeline hints at the storage driver rollout but does not confirm it -- watch whether the manager delegates verification before mitigation.",
        "Remove the suspected-cause sentence from the payload and compare the manager's first delegation.",
    ),
    "sequential-employee-onboarding": (
        "Each stage consumes an artifact: role profile -> proposed access list -> security-trimmed plan -> payroll actions. Check the chain survives intact.",
        "Change the role to a contractor in the payload and watch which downstream stages adapt.",
    ),
    "concurrent-vendor-risk-assessment": (
        "The payload sets a 150k USD budget cap and a two-week deadline -- finance and operations should engage those constraints, not restate generic risk.",
        "Raise the budget cap above the vendor's cost and compare the finance lane's verdict.",
    ),
    "handoff-customer-entitlement": (
        "Entitlement loss after renewal could be billing, contract, or engineering -- check the triage ROUTE rationale names evidence, not just a category.",
        "Add 'the order form shows the module was dropped at renewal' to the payload and confirm the route moves to contracts.",
    ),
    "group-chat-quarterly-planning": (
        "Headcount is frozen -- every proposed commitment should name what it trades away. Check the FINAL PLAN honors the freeze.",
        "Lift the freeze in the payload and compare which stakeholder wins more scope.",
    ),
    "magentic-supply-chain-disruption": (
        "The expedite budget is capped at 250k USD with contractual penalties in play -- watch whether the manager weighs expedite cost against penalty exposure.",
        "Double the expedite cap in the payload and compare the finance specialist's recommendation.",
    ),
    "sequential-procurement-approval": (
        "POL-PROC-01 says the vendor's review is expired, but POL-PROC-03 allows a 30-day regional-processing exception with security sign-off -- the legal stage should reconcile the two.",
        "Ask for the same vendor without the migration context and check whether the packet recommendation changes.",
    ),
    "concurrent-security-alert-enrichment": (
        "ALERT-2298 carries token_rotation_completed: False while POL-SEC-04 demands rotation within one hour -- the identity lane should flag the gap and the summary should escalate it.",
        "Flip token_rotation_completed to True in the fixture cell and compare the identity lane and final summary.",
    ),
    "handoff-claims-exception-routing": (
        "CLAIM-88120 has one fraud signal, so POL-CLM-09 routes fraud-first even though the amount also exceeds auto-approval -- check the ROUTE line honors that.",
        "Route CLAIM-88121 instead: it carries both a fraud signal and a compliance hold, so the fraud-first rule and the hold compete.",
    ),
    "group-chat-policy-exception-board": (
        "The request asks for 90 days but POL-GOV-03 caps waivers at 60 -- the chair's recorded expiry should reflect the cap, not the request.",
        "Change the request to 45 days in the payload and confirm the board approves without the cap discussion.",
    ),
    "magentic-business-continuity-drill": (
        "FACILITY-DC-WEST has a current drill while DC-EAST is 410 days overdue -- watch how the manager scopes the drill when a contrast site exists.",
        "Ask for a drill plan covering both facilities and compare how the manager splits the specialists.",
    ),
    "scenario-16-quote-to-cash-sequential": (
        "The request targets a 25 percent discount, which crosses the Legal (>20%) approval threshold -- the pricing stage should surface the required approval.",
        "Lower the discount to 15 percent in the payload and confirm the legal-approval requirement disappears.",
    ),
    "scenario-16-quote-to-cash-concurrent": (
        "The product-fit and pricing lanes discover SKUs independently -- check whether their SKU sets disagree and how the synthesizer reconciles them.",
        "Switch the payload to opportunity OPP-5002 -- its trigger is blocked -- and watch how the lanes and the synthesizer report a quote that cannot proceed.",
    ),
    "scenario-16-quote-to-cash-handoff": (
        "The trigger agent names the specialist the quote needs most; whichever route it picks, QuoteGenerationAgent must still finish the package.",
        "Reword the request to emphasize legal terms and confirm the ROUTE moves to the pricing/terms specialist.",
    ),
    "scenario-16-quote-to-cash-group-chat": (
        "The 25 percent discount gives the pricing reviewer a real objection -- check the debate surfaces the legal-approval requirement before the readiness verdict.",
        "Repoint the quote at customer ACC-3301 (mid-market terms) and compare how the pricing and legal reviewers' objections change.",
    ),
    "group-chat-partner-launch-review": (
        "The partner certification expires mid launch window and one compliance finding is open -- both facts live only behind the A2A seats, so the chair's verdict must cite what the remote agents reported.",
        "Edit PARTNER_FIXTURES so the certification renews before the window opens, rerun the server cell onward, and compare the FINAL RECOMMENDATION.",
    ),
    "scenario-16-quote-to-cash-magentic": (
        "The discount crosses the legal threshold, so the manager should delegate to pricing/terms before formatting the package -- watch the delegation order.",
        "Lower the discount to 15 percent in the payload and compare the manager's plan.",
    ),
    "sequential-loan-origination": (
        "LOAN-73021 passes every stage cleanly while POL-LEND-01 sets referral limits at DTI 0.43 and LTV 0.90 -- the offer packet should state why no manual referral was needed.",
        "Point the payload at LOAN-73022 (DTI 0.44, LTV 0.92) and watch the risk-pricing stage refer the file instead of pricing it.",
    ),
    "concurrent-ma-due-diligence": (
        "Each lane finds a different red flag on TARGET-ACQ-STELLAR (customer concentration, open litigation, missing SOC 2) -- under the POL-MA-02 gate the deal lead cannot recommend a clean proceed.",
        "Switch the payload to TARGET-ACQ-HARBOR (clean but slower-growing) and compare the lanes' findings and the final recommendation.",
    ),
    "handoff-transaction-dispute": (
        "DISPUTE-90455 carries both a merchant-error signal (duplicate posting) and a fraud signal (lost card) -- POL-DSP-04 says fraud review wins that tie; check the ROUTE line honors it.",
        "Switch the payload to DISPUTE-90456 (a post-cancellation subscription charge with no fraud signal) and confirm the route moves to the subscription specialist.",
    ),
    "group-chat-architecture-review": (
        "ADR-2209 gives every seat a real objection -- US-only vendor data residency, 85 percent platform utilization, 96k per year -- watch which concern the DECISION line resolves with conditions.",
        "Reword the payload to say the vendor now offers an EU data region and see whether the chair's decision flips or just loses a condition.",
    ),
    "magentic-churn-spike-investigation": (
        "Three candidate causes overlap the spike window (pricing change, billing migration, P1 outages) -- watch whether the manager delegates elimination work before accepting a driver.",
        "Remove the pricing-change mention from the payload and compare which specialist the manager schedules first.",
    ),
}

#: Per-pattern row for the cross-pattern comparison table rendered in every
#: notebook: (control flow, coordination cost, latency and cost, fails when,
#: choose it when). Keep cells short -- the five rows render side by side.
PATTERN_COMPARISON_ROWS: dict[str, tuple[str, str, str, str, str]] = {
    "sequential": (
        "Fixed pipeline; each stage consumes the previous stage's output",
        "None at runtime -- the graph is the plan",
        "Slowest wall-clock for independent work; easiest to debug and audit",
        "A stage needs information only a later stage produces",
        "The order is mandated: compliance gates, artifact chains, staged approvals",
    ),
    "concurrent": (
        "One fan-out to parallel lanes, one code-defined fan-in",
        "None between lanes; the fan-in labels and combines",
        "Best wall-clock when lanes are truly independent",
        "Lanes secretly depend on each other's findings",
        "Independent expert reviews of the same input, under time pressure",
    ),
    "handoff": (
        "Triage names one owner; a router validates the choice",
        "One routing decision, code-checked against allowed routes",
        "Cheapest -- only the owner (plus an optional finisher) runs",
        "The case genuinely needs several specialists to collaborate",
        "Ownership depends on case facts and most specialists should not run",
    ),
    "group-chat": (
        "Round-robin turns in a shared transcript; a closer ends each cycle",
        "High -- every turn rereads the whole discussion",
        "Slow and token-hungry; the transcript itself is the product",
        "Participants never actually react to each other",
        "Deliberation and critique must be visible in a recorded decision",
    ),
    "magentic": (
        "A manager plans, delegates, observes a ledger, and replans",
        "Highest -- planning, delegation, and replan loops",
        "Most expensive and least predictable run shape",
        "The task was really a known pipeline all along",
        "Ambiguous work where the plan must change as evidence arrives",
    ),
}

#: Per-scenario pattern notes shared by both projects: how the taught pattern
#: executes THIS scenario (role-based, since rosters differ per package) and an
#: honest verdict on which pattern we would actually choose for the problem.
SCENARIO_PATTERN_NOTES: dict[str, dict[str, str]] = {
    "sequential-release-readiness": {
        "walkthrough": (
            "The job arrives naming the release scope and two hard constraints: a finance-freeze "
            "date and a rollback requirement. The intake stage turns it into a work order, the "
            "dependency stage audits what the release touches, the risk stage classifies severity "
            "using the dependency findings, the evidence stage checks test proof, and the final "
            "stage writes the go/no-go brief. Each stage reads the original request plus everything "
            "produced before it, so the brief can cite the freeze and the rollback plan without "
            "re-deriving them."
        ),
        "verdict": (
            "Sequential is the right call. The stages have real data dependencies -- risk "
            "classification is meaningless before the dependency audit -- so concurrent lanes would "
            "each rebuild the same context, and a group chat would add turn-taking cost without "
            "adding information. Reach for concurrent only if your gates become genuinely "
            "independent checklists."
        ),
    },
    "concurrent-pr-review": {
        "walkthrough": (
            "One diff summary fans out to four reviewers at once -- security, performance, tests, "
            "and style -- each judging only its own lane. A code-defined aggregator labels each "
            "verdict with its lane and stitches the findings into one review, so no reviewer waits "
            "on, or is anchored by, another."
        ),
        "verdict": (
            "Concurrent wins. The lanes are independent by construction (a security opinion does "
            "not depend on a style opinion), so running them in order only slows the review down, "
            "and a group chat would let early speakers anchor later ones. Sequential earns its "
            "place only when one reviewer's output feeds another's judgment."
        ),
    },
    "handoff-support-triage": {
        "walkthrough": (
            "The ticket deliberately mixes symptoms: exports fail right after SSO login, which "
            "reads as auth, billing, or export depending on which detail you weight. Triage reads "
            "the ticket, names one owner in a ROUTE line, and a code-defined router validates that "
            "choice against the allowed specialists (falling back to keyword scoring) before "
            "exactly one specialist answers."
        ),
        "verdict": (
            "Handoff is the right call: only one specialist should spend tokens per ticket, and "
            "ownership genuinely depends on the ticket's content. Concurrent would wake every "
            "specialist for every ticket; sequential would force a fixed order onto a decision "
            "that is the whole point. If tickets routinely needed several specialists to "
            "collaborate, magentic or group chat would enter the conversation."
        ),
    },
    "group-chat-launch-council": {
        "walkthrough": (
            "Four advisors and a facilitator debate one question -- launch this week or hold -- in "
            "a visible round-robin transcript. Each advisor reacts to what has already been said "
            "(the reliability advisor can rebut the QA advisor's evidence), and the facilitator "
            "closes each cycle; the chat ends when the facilitator's turn carries the FINAL "
            "RECOMMENDATION line or the cycle cap is reached."
        ),
        "verdict": (
            "Group chat earns its cost here because the advisors' concerns interact -- two timeout "
            "reports matter less once rollback-by-feature-flag is on the table, and only a shared "
            "transcript surfaces that rebuttal. If your advisors never need to answer each other, "
            "concurrent with a synthesizer gives the same coverage faster and cheaper."
        ),
    },
    "magentic-incident-response": {
        "walkthrough": (
            "The payload is a timeline of symptoms with a suspected but unconfirmed cause. The "
            "manager plans an investigation, delegates verification and mitigation to specialists, "
            "watches the progress ledger, and replans when a delegation stalls or a finding changes "
            "the picture -- the run's shape is decided at runtime, not in the graph."
        ),
        "verdict": (
            "Magentic fits because the incident's shape is unknown up front: if verification "
            "disproves the storage-driver theory the plan must change, and no fixed pipeline can "
            "encode that. Handoff could route the incident to one owner but cannot replan; "
            "sequential would hard-code an investigation order the evidence might contradict. Once "
            "your incidents follow a stable runbook, sequential over that runbook is cheaper and "
            "more auditable."
        ),
    },
    "sequential-employee-onboarding": {
        "walkthrough": (
            "HR produces the role profile; IT provisions against that profile; security reviews "
            "what IT provisioned; payroll enrolls against the confirmed profile; enablement builds "
            "the first-week plan from all of it. Every stage consumes a concrete artifact from the "
            "stage before, which is exactly what this pattern is for."
        ),
        "verdict": (
            "Sequential is correct because of the artifact chain -- IT cannot provision before HR "
            "defines the role, and security reviews IT's output, not the intake form. The honest "
            "caveat lives in the scenario's own when-to-use note: if your departments only shared "
            "the intake payload and produced independent checklists, concurrent would finish "
            "faster."
        ),
    },
    "concurrent-vendor-risk-assessment": {
        "walkthrough": (
            "One vendor intake fans out to five independent risk lanes -- security, privacy, "
            "legal, finance, operations -- each applying its own criteria to the same request and "
            "its budget cap. Fan-in labels each lane's finding, so the combined assessment "
            "preserves who said what."
        ),
        "verdict": (
            "Concurrent wins: the five reviews share input but not reasoning, and the two-week "
            "decision deadline rewards parallel wall-clock. Sequential adds latency with no "
            "dependency payoff. If the lanes needed to negotiate -- finance trading scope against "
            "security's demands -- group chat would become the honest choice."
        ),
    },
    "handoff-customer-entitlement": {
        "walkthrough": (
            "A strategic account lost a purchased feature after renewal while billing still shows "
            "the subscription active -- so the owner could plausibly be billing, contract, "
            "support, or engineering. Triage weighs the case facts, names the owner in a ROUTE "
            "line, and the router validates it before the single specialist resolves the case."
        ),
        "verdict": (
            "Handoff is right: the case needs one accountable owner chosen from context, on a "
            "same-day clock. Concurrent would draft four conflicting answers for one customer; "
            "magentic's planning loop is overkill for a single routing decision. If entitlement "
            "cases regularly required multi-team fixes, a manager-led magentic flow would start "
            "to pay."
        ),
    },
    "group-chat-quarterly-planning": {
        "walkthrough": (
            "Stakeholders with competing asks negotiate one operating plan under a frozen-headcount "
            "constraint. Every proposal lands in the shared transcript where the next stakeholder "
            "must respond to it, and the closing planner ends a converged cycle with the FINAL "
            "PLAN line."
        ),
        "verdict": (
            "Group chat is the honest fit: planning under a shared constraint is a negotiation, "
            "and the medium of negotiation is exactly a transcript where commitments can be "
            "challenged. Concurrent would collect five wish lists that still need reconciling; "
            "sequential would give whoever goes last the only veto. The runner-up is magentic with "
            "a planning manager, which trades the visible debate for speed."
        ),
    },
    "magentic-supply-chain-disruption": {
        "walkthrough": (
            "A disruption threatens two product lines under an expedite-budget cap and contractual "
            "penalties. The manager plans response options, delegates costing and feasibility to "
            "specialists, and replans as quotes and constraints come back -- the option set at the "
            "end is not knowable at the start."
        ),
        "verdict": (
            "Magentic fits because the response is genuinely open-ended: which specialists matter "
            "depends on which options survive costing, and that is a replanning loop by "
            "definition. Group chat could debate a known option set but cannot generate and retire "
            "options iteratively. If your disruptions resolve with a fixed escalation checklist, "
            "sequential is cheaper."
        ),
    },
    "sequential-procurement-approval": {
        "walkthrough": (
            "The job walks VENDOR-4471 through intake, budget, security, legal, and packet stages "
            "in policy order. Each stage grounds its check in MCP tools -- the vendor record, the "
            "spend policy, the security-review status -- and the packet stage assembles what every "
            "prior stage found into one go/no-go recommendation with a decision-log entry."
        ),
        "verdict": (
            "Sequential is the taught and defensible choice: approval chains are audited as "
            "ordered gates, and the packet must cite each gate's finding. The honest observation "
            "is that budget, security, and legal each read the same vendor record independently, "
            "so concurrent lanes feeding a packet synthesizer would reach the same answer faster "
            "-- choose sequential when auditability and fixed order are requirements, not "
            "conveniences."
        ),
    },
    "concurrent-security-alert-enrichment": {
        "walkthrough": (
            "ALERT-2298 fans out to four enrichment lanes -- identity, endpoint, network, and "
            "data-loss -- each pulling its own slice of context from the MCP tools. The lanes fan "
            "in with labels, and the summary agent, held out of the fan-out, reads all four to "
            "assemble the incident summary."
        ),
        "verdict": (
            "Concurrent is exactly right: enrichment lanes are independent reads against the same "
            "alert, minutes matter, and the synthesizer-after-fan-in shape means the agent that "
            "writes the summary actually saw every lane. Sequential enrichment would serialize "
            "work with no ordering constraint; magentic would add planning overhead to a task "
            "whose shape never changes."
        ),
    },
    "handoff-claims-exception-routing": {
        "walkthrough": (
            "CLAIM-88120 exceeds the auto-approval threshold and carries a fraud signal, so per "
            "POL-CLM-09 triage must route fraud-first even though a payment specialist also has a "
            "claim on it. The router validates the ROUTE line, the fraud specialist investigates, "
            "and the communication agent always finishes with the customer message."
        ),
        "verdict": (
            "Handoff wins because policy makes ownership conditional on case facts -- the same "
            "claim without a fraud signal routes elsewhere -- and the finisher guarantees every "
            "path ends with a customer communication. Sequential would run specialists the claim "
            "does not need; group chat would debate what policy has already decided."
        ),
    },
    "group-chat-policy-exception-board": {
        "walkthrough": (
            "The board debates POLICY-EX-77: a 90-day residency waiver request against a policy "
            "that caps waivers at 60 days. Risk, business need, and compliance each ground their "
            "argument in MCP facts, and the chair closes each cycle -- approving only with a "
            "compensating control and an expiry that respects the cap."
        ),
        "verdict": (
            "Group chat is the right instrument for a governance board: the output is not just a "
            "decision but a documented deliberation, and the compensating control typically "
            "emerges from compliance answering risk in-transcript. Concurrent position papers "
            "would leave the 90-versus-60-day conflict unresolved; a single handoff owner cannot "
            "represent three interests."
        ),
    },
    "magentic-business-continuity-drill": {
        "walkthrough": (
            "The manager scopes a drill for FACILITY-DC-EAST, 410 days overdue, while "
            "FACILITY-DC-WEST offers a current-drill contrast. It delegates facility, IT, "
            "communications, finance, and operations planning, and replans as the scope firms up."
        ),
        "verdict": (
            "Magentic is defensible because the scoping decision -- what the drill must cover "
            "given two facilities and shared dependencies -- benefits from a manager weighing "
            "specialist input and replanning. The honest runner-up is sequential over the "
            "continuity-drill playbook: if your drill scope is settled up front, the five playbook "
            "steps are a pipeline and magentic's planning loop is overhead."
        ),
    },
    "scenario-16-quote-to-cash-sequential": {
        "walkthrough": (
            "The quote for OPP-5001 builds in dependency order: the trigger confirms the request "
            "is quotable, customer context sets the terms baseline, SKU discovery and product fit "
            "define what is being sold, pricing applies the 25 percent discount that crosses the "
            "legal threshold, and quote generation packages everything with the required legal "
            "approval flagged."
        ),
        "verdict": (
            "For quote-to-cash, sequential is the pattern we would actually ship: each stage "
            "consumes the previous stage's output (you cannot price SKUs you have not validated), "
            "and the audit trail mirrors the pipeline. Compare 16b-16e to see the same roles under "
            "the other patterns -- instructive, but each pays a coordination cost this business "
            "process does not need."
        ),
    },
    "scenario-16-quote-to-cash-concurrent": {
        "walkthrough": (
            "The same six roles run as self-sufficient lanes: each parallel lane re-derives the "
            "context it needs (trigger, customer, SKUs, pricing) independently, and the quote "
            "owner is held out of the fan-out to reconcile the lanes' possibly-disagreeing "
            "findings after fan-in."
        ),
        "verdict": (
            "Honestly, sequential (16a) fits quote-to-cash better -- the lanes here overlap in "
            "what they read and can disagree about SKUs, which is exactly why the synthesizer must "
            "reconcile them. Concurrent earns its keep when quote volume makes wall-clock the "
            "constraint and reconciliation is cheap; this variant teaches that tradeoff "
            "deliberately."
        ),
    },
    "scenario-16-quote-to-cash-handoff": {
        "walkthrough": (
            "The trigger agent triages the request and routes to the single specialist the quote "
            "needs most -- customer context, SKU discovery, product fit, or pricing -- and the "
            "quote owner always finishes the package regardless of route."
        ),
        "verdict": (
            "This variant is instructive overkill: a real quote eventually needs all of these "
            "roles, so routing to just one is only right for narrow exception passes such as a "
            "pricing-only revision. We would choose sequential (16a) for a full quote; handoff "
            "shines in flows like scenarios 13 and 21 where most specialists genuinely should not "
            "run."
        ),
    },
    "scenario-16-quote-to-cash-group-chat": {
        "walkthrough": (
            "The quote's reviewers debate readiness, product fit, SKU validity, and the "
            "over-threshold discount in a shared transcript, and the quote owner closes each cycle "
            "-- terminating with the final quote recommendation once the objections have been "
            "answered."
        ),
        "verdict": (
            "Group chat is worth its token bill only for exception quotes -- the 25 percent "
            "discount gives the pricing reviewer a genuine objection worth debating. For routine "
            "quotes we would use sequential (16a) and reserve this board for deals that trip a "
            "policy threshold, which is exactly how change-advisory boards work in practice."
        ),
    },
    "scenario-16-quote-to-cash-magentic": {
        "walkthrough": (
            "A quote manager plans the work, delegates to the customer, SKU, product-fit, and "
            "pricing specialists in whatever order the request demands, monitors the ledger, and "
            "replans -- here, discovering the discount crosses the legal threshold and delegating "
            "terms review before packaging."
        ),
        "verdict": (
            "Magentic is the heaviest tool in the box, and a routine quote does not need it -- "
            "sequential (16a) produces the same package predictably. This variant teaches when you "
            "would upgrade: quotes that fail in unpredictable ways (blocked triggers, incompatible "
            "SKUs, contested terms) reward a manager that can reorder the work mid-run."
        ),
    },
    "group-chat-partner-launch-review": {
        "walkthrough": (
            "The launch council seats five voices, two of which are remote partner agents reached "
            "over A2A -- discovered by agent card and called over JSON-RPC. The "
            "certification-expiry and open-finding facts live only behind those remote seats, so "
            "the chair's FINAL RECOMMENDATION must cite what the partners reported; the "
            "orchestration itself is the same group chat used elsewhere in this repo."
        ),
        "verdict": (
            "Group chat is the right pattern for a joint review where each organization must hear "
            "and answer the others' constraints in one transcript. The A2A lesson is orthogonal: "
            "any pattern can seat a remote agent. If the partners only needed to file reports "
            "rather than deliberate, concurrent lanes calling the same A2A endpoints would be "
            "cheaper."
        ),
    },
    "sequential-loan-origination": {
        "walkthrough": (
            "LOAN-73021 walks the mandated stages in order: intake normalizes the application, "
            "credit analysis checks the score against POL-LEND-01's referral limits, income "
            "verification recomputes the debt-to-income ratio, risk pricing assigns the tier or "
            "refers the file, and the offer packet records the decision. Each stage builds on "
            "verified facts from the previous one -- income verification confirms the very ratio "
            "credit analysis relied on."
        ),
        "verdict": (
            "Sequential is the textbook choice, which is why this scenario exists: lending "
            "regulation mandates the stage order, a skipped check is a compliance failure, and the "
            "marginal file LOAN-73022 shows the pipeline correctly diverting to manual "
            "underwriting. No other pattern can promise that every application takes the same "
            "auditable path."
        ),
    },
    "concurrent-ma-due-diligence": {
        "walkthrough": (
            "Four diligence lanes attack TARGET-ACQ-STELLAR at once -- finance finds the "
            "customer-concentration risk, legal the open litigation, technology the missing SOC 2, "
            "market the churn story -- and the deal lead, held out of the fan-out, applies the "
            "POL-MA-02 gate to the labelled findings: any unmitigated red flag blocks a proceed."
        ),
        "verdict": (
            "Concurrent is the textbook choice: the workstreams are independent by professional "
            "design (legal does not wait for finance), deal timelines punish serialization, and "
            "the synthesizer-after-fan-in shape guarantees the recommendation was written by an "
            "agent that saw every lane. Sequential would roughly quadruple wall-clock for zero "
            "dependency benefit."
        ),
    },
    "handoff-transaction-dispute": {
        "walkthrough": (
            "DISPUTE-90455 carries conflicting signals -- a duplicate posting says merchant error, "
            "a lost-card report says fraud -- and POL-DSP-04 breaks the tie: any fraud indicator "
            "routes to fraud review before provisional credit. Triage names the owner in a ROUTE "
            "line, the router validates it, the specialist resolves the case, and the "
            "communications agent always closes with the customer letter and the regulatory clock."
        ),
        "verdict": (
            "Handoff is the textbook choice: routing is the decision -- running the merchant-error "
            "specialist on a fraud case is precisely the mistake the policy exists to prevent -- "
            "most specialists must not run, and the finisher guarantees the regulated customer "
            "communication. Concurrent would produce contradictory resolutions; the contrast case "
            "DISPUTE-90456 shows the route flipping cleanly."
        ),
    },
    "group-chat-architecture-review": {
        "walkthrough": (
            "ADR-2209 gives every seat a genuine objection -- platform engineering argues the "
            "two-quarter build against 85 percent utilization, security argues the vendor's "
            "US-only data region, finance argues the 96k annual cost, delivery argues on-call load "
            "-- and the chair closes each cycle, ending with a DECISION line that carries "
            "conditions and an exit strategy."
        ),
        "verdict": (
            "Group chat is the textbook choice: build-versus-buy is decided by tradeoffs that live "
            "in different heads, the decision is only defensible if the objections were visibly "
            "answered, and the transcript is the decision record POL-ARCH-07 requires. Concurrent "
            "position papers would leave residency-versus-capacity unresolved; one handoff owner "
            "cannot represent four interests."
        ),
    },
    "magentic-churn-spike-investigation": {
        "walkthrough": (
            "The manager starts from METRIC-CHURN-Q3 -- churn more than doubled while support "
            "tickets stayed flat -- and three candidate causes overlapping the spike window. It "
            "delegates quantification first, then billing, pricing, and reliability "
            "investigations in whatever order the evidence suggests, replans as candidates are "
            "eliminated, and hands the surviving driver to the retention planner for remediation."
        ),
        "verdict": (
            "Magentic is the textbook choice: the investigation's shape is unknowable up front -- "
            "eliminating the pricing theory changes what to ask next -- and that replanning loop "
            "is the pattern's whole value. A sequential pipeline would hard-code an investigation "
            "order the evidence might contradict; concurrent lanes would investigate all three "
            "causes fully even after one is disproven."
        ),
    },
}

PATTERN_ORDER = ("sequential", "concurrent", "handoff", "group-chat", "magentic")


def pattern_comparison_table(current: str | None) -> str:
    """Markdown table comparing all five patterns, highlighting ``current``."""

    lines = [
        "| Pattern | Control flow | Coordination cost | Latency and cost | Fails when | Choose it when |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for pattern in PATTERN_ORDER:
        control, coordination, latency, fails, choose = PATTERN_COMPARISON_ROWS[pattern]
        label = pattern.replace("-", " ")
        if pattern == current:
            label = f"**{label} (this notebook)**"
        lines.append(f"| {label} | {control} | {coordination} | {latency} | {fails} | {choose} |")
    return "\n".join(lines)


def _pattern_seat_line(scenario: Any) -> str:
    """One sentence mapping this project's actual roster onto the pattern shape."""

    names = [f"`{spec.name}`" for spec in scenario.agents]
    if scenario.pattern == "sequential":
        return "In this notebook the stages run " + " -> ".join(names) + "."
    if scenario.pattern == "concurrent":
        synthesizer = getattr(scenario, "concurrent_synthesizer", None)
        lanes = [name for name in names if name != f"`{synthesizer}`"] if synthesizer else names
        line = "In this notebook the parallel lanes are " + ", ".join(lanes)
        if synthesizer:
            line += f", and `{synthesizer}` runs after fan-in to combine them"
        return line + "."
    if scenario.pattern == "handoff":
        finisher = getattr(scenario, "handoff_finisher", None)
        specialists = [name for name in names[1:] if name != f"`{finisher}`"] if finisher else names[1:]
        line = f"In this notebook {names[0]} triages and the router hands off to one of " + ", ".join(specialists)
        if finisher:
            line += f"; `{finisher}` always finishes"
        return line + "."
    if scenario.pattern == "group-chat":
        return (
            "In this notebook the speaking order is "
            + " -> ".join(names)
            + ", cycling until the closer's verdict (or the cycle cap) ends the chat."
        )
    return f"In this notebook {names[0]} is the manager and the specialists are " + ", ".join(names[1:]) + "."


def pattern_deep_dive_markdown(project: dict[str, str], scenario: Any) -> str:
    notes = SCENARIO_PATTERN_NOTES[scenario.id]
    pattern_heading = scenario.pattern.replace("-", " ").title()
    return f"""
    ## How {pattern_heading} Plays Out in This Scenario

    {notes["walkthrough"]}

    {_pattern_seat_line(scenario)}

    ## Pattern Comparison

    {pattern_comparison_table(scenario.pattern)}

    > **Which pattern would we actually choose?** {notes["verdict"]}
    """


def primitives_pattern_comparison_markdown() -> str:
    return f"""
    ## Pattern Comparison

    This lab runs all five orchestration builders over the same roster, so keep this comparison
    close while you work through the pattern cells below -- each row summarizes what you are
    about to see the builders do differently.

    {pattern_comparison_table(None)}

    > **Which pattern would we actually choose?** For this enablement brief the honest answer is
    > sequential -- the deliverable is a fixed document with known sections. The lab intentionally
    > runs every builder anyway, because its job is to show the mechanics side by side; scenarios
    > 19-23 each pick the single best-fit pattern for a real business case.
    """

def cell_source(source: str) -> list[str]:
    text = textwrap.dedent(source).strip("\n")
    lines = text.splitlines()
    first = next((line for line in lines if line.strip()), "")
    if first.startswith("    "):
        lines = [line[4:] if line.startswith("    ") else line for line in lines]
    return [f"{line}\n" for line in lines]


def md(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": cell_source(source)}


def code(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": cell_source(source),
    }


#: Lead-in badges that let a reader tell framework surface from glue at a glance.
#: Kept as literal, greppable strings so the split can be verified mechanically.
PRIMITIVE = "**Agent Framework primitive.**"
SUPPORT = "**Supporting code.**"


def teach(title: str, tag: str, body: str, code_source: str) -> list[dict[str, Any]]:
    """One teaching unit: a titled, tagged markdown lead-in + one runnable code cell.

    ``tag`` is ``PRIMITIVE`` (introduces an Agent Framework class/call) or
    ``SUPPORT`` (scaffolding/glue). ``body`` says why the code exists and what it does.
    """

    explanation = f"### {title}\n\n{tag} {body}"
    return [md(explanation), code(code_source)]


def add_cell_ids(cells: list[dict[str, Any]], scenario_id: str) -> None:
    safe_id = "".join(char if char.isalnum() or char == "-" else "-" for char in scenario_id)
    prefix = safe_id[:56].strip("-") or "scenario"
    for index, cell in enumerate(cells):
        cell["id"] = f"{prefix}-{index:02d}"


def load_scenarios(project: dict[str, str]) -> tuple[Any, ...]:
    src = ROOT / project["folder"] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    module = importlib.import_module(f"{project['package']}.scenarios")
    return tuple(module.SCENARIOS)


def notebook_paths_by_id(project: dict[str, str], scenarios: tuple[Any, ...]) -> dict[str, Path]:
    scenario_ids = {scenario.id for scenario in scenarios}
    result: dict[str, Path] = {}
    for path in sorted((ROOT / project["folder"] / "notebooks").glob("*.ipynb")):
        text = path.read_text(encoding="utf-8")
        matches = [scenario_id for scenario_id in scenario_ids if scenario_id in text]
        if len(matches) != 1:
            raise RuntimeError(f"Could not identify scenario for {path}: {matches}")
        result[matches[0]] = path
    missing = scenario_ids - set(result)
    for scenario_id in sorted(missing):
        filename = NEW_NOTEBOOK_FILENAMES.get(scenario_id)
        if filename is None:
            raise RuntimeError(f"Missing notebook for {scenario_id} and no filename registered.")
        result[scenario_id] = ROOT / project["folder"] / "notebooks" / filename
    return result


#: Filenames for scenarios whose notebooks do not exist yet.
NEW_NOTEBOOK_FILENAMES = {
    "group-chat-partner-launch-review": "17-group-chat-partner-launch-review.ipynb",
    PRIMITIVES_SCENARIO_ID: "18-agent-framework-primitives-lab.ipynb",
    "sequential-loan-origination": "19-sequential-loan-origination.ipynb",
    "concurrent-ma-due-diligence": "20-concurrent-ma-due-diligence.ipynb",
    "handoff-transaction-dispute": "21-handoff-transaction-dispute.ipynb",
    "group-chat-architecture-review": "22-group-chat-architecture-review.ipynb",
    "magentic-churn-spike-investigation": "23-magentic-churn-spike-investigation.ipynb",
}


def scenario_data(scenario: Any, sample_attr: str) -> dict[str, Any]:
    return {
        "id": scenario.id,
        "pattern": scenario.pattern,
        "title": scenario.title,
        "learning_goal": scenario.learning_goal,
        "when_to_use": scenario.when_to_use,
        "max_tokens": scenario.max_tokens,
        sample_attr: getattr(scenario, sample_attr),
        "handoff_finisher": getattr(scenario, "handoff_finisher", None),
        "concurrent_synthesizer": getattr(scenario, "concurrent_synthesizer", None),
        "termination_phrases": list(getattr(scenario, "termination_phrases", ()) or ()),
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "instructions": agent.instructions,
                "mcp_tools": list(agent.mcp_tools),
                "mcp_server": agent.mcp_server,
                "route_keywords": list(getattr(agent, "route_keywords", ()) or ()),
                "a2a_url": getattr(agent, "a2a_url", None),
            }
            for agent in scenario.agents
        ],
    }



def scenario_uses_a2a(scenario: Any) -> bool:
    return any(getattr(agent, "a2a_url", None) for agent in scenario.agents)


def a2a_markdown() -> str:
    return """
    ## A2A Partner Context

    Two council seats belong to *partner organizations* and are reached over the
    **A2A (Agent2Agent) protocol**. Where MCP connects an agent to tools, A2A connects an
    agent to *peer agents*: each partner publishes an agent card over HTTP and answers
    JSON-RPC messages; its model, instructions, and facts stay behind its own boundary.
    In production those agents run in the partner's infrastructure; this notebook hosts
    deterministic stand-ins in-process so every cell runs without credentials or a second
    terminal. The next cells walk the protocol on-ramp one step at a time: partner facts,
    partner behavior, hosting, agent-card discovery, and a direct client round-trip --
    all before any orchestration exists.
    """


def a2a_fixtures_cell() -> str:
    return r'''
    PARTNER_FIXTURES = {
        "partner-solutions": {
            "organization": "Fabrikam Integrations (ISV partner)",
            "integration_certification_expires": "2026-07-20",
            "launch_window": "2026-07-15 to 2026-07-31",
            "nightly_integration_tests": "47 passing, 1 failing (bulk-export, since Tuesday)",
            "connector_version": "2.3.1",
            "notes": "Certification expires mid launch window; the renewal audit is booked for 2026-07-18.",
        },
        "compliance": {
            "organization": "Meridian Assurance (external audit firm)",
            "soc2_status": "current",
            "joint_data_processing_addendum": "signed",
            "open_findings": 1,
            "open_finding_detail": "Partner telemetry retention is 120 days; the joint standard requires 90.",
            "notes": "The open finding needs a remediation date before joint go-live.",
        },
    }

    PARTNER_SEATS = {
        "partner-solutions": ("PartnerSolutionsAgent", "ISV partner agent: argues partner-side integration readiness."),
        "compliance": ("ExternalComplianceAgent", "External audit firm agent: argues certification and compliance status."),
    }


    def partner_reply(path: str, question: str | None = None) -> str:
        """The fixture-grounded answer a partner agent gives -- zero LLM calls.

        Question-aware but deterministic: fact keys whose words overlap the
        question are returned (plus notes); the full sheet is the fallback.
        """

        import re as _re

        facts = PARTNER_FIXTURES[path]
        name, _ = PARTNER_SEATS[path]
        selected = {key: value for key, value in facts.items() if key != "organization"}
        if question:
            words = {word for word in _re.findall(r"[a-z0-9]+", question.lower()) if len(word) > 3}
            matched = {key: value for key, value in selected.items() if set(key.split("_")) & words}
            if matched:
                matched.setdefault("notes", facts["notes"])
                selected = matched
        lines = [f"{name} ({facts['organization']}) reports:"]
        for key, value in selected.items():
            lines.append(f"- {key.replace('_', ' ')}: {value}")
        return "\n".join(lines)


    # Demo (offline): the partner behavior is a function over its facts, and it
    # answers the question it was asked -- compare the full sheet vs a targeted ask.
    print(partner_reply("partner-solutions"))
    print()
    print(partner_reply("partner-solutions", "When does the integration certification expire?"))
    '''


def a2a_server_cell() -> str:
    return r'''
    import socket
    import threading
    import time

    import uvicorn
    from starlette.applications import Starlette

    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

    from agent_framework import AgentResponse, BaseAgent, Message
    from agent_framework.a2a import A2AExecutor


    class DeterministicPartnerAgent(BaseAgent):
        """The agent behind the A2A endpoint: answers from PARTNER_FIXTURES."""

        def __init__(self, path: str, **kwargs) -> None:
            super().__init__(**kwargs)
            self._path = path

        async def run(self, messages=None, *, session=None, **kwargs):
            question = messages if isinstance(messages, str) else getattr(messages, "text", "") or ""
            if isinstance(messages, (list, tuple)):
                question = " ".join(getattr(m, "text", "") or str(m) for m in messages)
            reply = partner_reply(self._path, question)
            return AgentResponse(messages=[Message(role="assistant", contents=[reply])])

        async def run_stream(self, messages=None, *, session=None, **kwargs):
            yield await self.run(messages, session=session, **kwargs)


    def _partner_routes(path: str, base_url: str) -> list:
        name, description = PARTNER_SEATS[path]
        card = AgentCard(
            name=name,
            description=description,
            version="1.0.0",
            supported_interfaces=[AgentInterface(url=f"{base_url}/{path}", protocol_binding="JSONRPC")],
            capabilities=AgentCapabilities(streaming=False),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            skills=[AgentSkill(id=f"{path}-launch-review", name="Joint launch review", description=description, tags=["a2a"])],
        )
        executor = A2AExecutor(DeterministicPartnerAgent(path, name=name, description=description))
        handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore(), agent_card=card)
        # Flat prefixed routes: the JSON-RPC endpoint lives at exactly /<path>.
        return create_agent_card_routes(
            card, card_url=f"/{path}/.well-known/agent-card.json"
        ) + create_jsonrpc_routes(handler, rpc_url=f"/{path}")


    with socket.socket() as _sock:
        _sock.bind(("127.0.0.1", 0))
        A2A_PORT = _sock.getsockname()[1]
    A2A_BASE_URL = f"http://127.0.0.1:{A2A_PORT}"

    _routes = []
    for _path in PARTNER_SEATS:
        _routes.extend(_partner_routes(_path, A2A_BASE_URL))
    _app = Starlette(routes=_routes)
    _uvicorn_server = uvicorn.Server(uvicorn.Config(_app, host="127.0.0.1", port=A2A_PORT, log_level="error"))
    threading.Thread(target=_uvicorn_server.run, daemon=True).start()
    _deadline = time.time() + 10
    while not _uvicorn_server.started:
        if time.time() > _deadline:
            raise RuntimeError("Partner A2A server did not start.")
        time.sleep(0.05)

    os.environ["A2A_PARTNER_BASE_URL"] = A2A_BASE_URL
    print(f"Partner A2A server up: {A2A_BASE_URL}  (seats: " + ", ".join(n for n, _ in PARTNER_SEATS.values()) + ")")
    '''


def a2a_discovery_cell() -> str:
    return r'''
    import httpx

    # Demo (offline): protocol discovery -- fetch each partner's agent card over HTTP.
    for _path, (_name, _desc) in PARTNER_SEATS.items():
        _card = httpx.get(f"{A2A_BASE_URL}/{_path}/.well-known/agent-card.json", timeout=5).json()
        _iface = (_card.get("supportedInterfaces") or [{}])[0]
        print(f"{_card.get('name')}: {_iface.get('url')} [{_iface.get('protocolBinding', 'JSONRPC')}]")
        print(f"  {_card.get('description')}")
    '''


def a2a_client_cell() -> str:
    return r'''
    from agent_framework.a2a import A2AAgent

    # Demo (offline): one direct A2A round-trip before any orchestration exists.
    _partner = A2AAgent(name="PartnerSolutionsAgent", url=f"{A2A_BASE_URL}/partner-solutions")
    _reply = await _partner.run("Report partner-side launch readiness for the July window.")
    render_transcript("[PartnerSolutionsAgent] " + (_reply.text or ""))
    '''


def scenario_uses_mcp(scenario: Any) -> bool:
    return any(agent.mcp_tools for agent in scenario.agents)


def scenario_mcp_server(scenario: Any) -> str | None:
    servers = {agent.mcp_server for agent in scenario.agents if agent.mcp_tools}
    if not servers:
        return None
    if len(servers) != 1:
        raise RuntimeError(f"{scenario.id} uses multiple MCP servers: {servers}")
    return next(iter(servers))


def _agent_capability_label(agent: Any) -> str:
    """Short display string of agent capabilities for the roster table."""
    mcp_tools = list(getattr(agent, "mcp_tools", ()) or ())
    if mcp_tools:
        return "Domain tools: " + ", ".join("`" + t + "`" for t in mcp_tools)
    return "Instructions only"


def title_markdown(project: dict[str, str], scenario: Any) -> str:
    return f"""
    # {scenario.title}

    | Field | Value |
    | --- | --- |
    | Scenario id | `{scenario.id}` |
    | Pattern | `{scenario.pattern}` |
    | API | `{project['api_name']}` |
    | Recommended max tokens | `{scenario.max_tokens}` per agent turn |

    **Learning goal:** {scenario.learning_goal}

    > {scenario.when_to_use}
    """


def concept_markdown(project: dict[str, str], scenario: Any) -> str:
    concept, best_fit = PATTERN_DOCS[scenario.pattern]

    if project["sample_attr"] == "sample_input":
        api_note = (
            "**Responses API -- startup-selected scenario shape.** "
            "The scenario and orchestration pattern are wired in at server start. "
            "Each client request uses the standard OpenAI-compatible `/responses` body -- "
            "a plain chat-style input. The client never specifies which agents run; "
            "the server owns the orchestration entirely."
        )
    else:
        api_note = (
            "**Invocations API -- per-request job payload shape.** "
            "Each request body carries `scenario`, `pattern`, `task`, `artifacts`, and "
            "`constraints`. The caller controls which orchestration runs per invocation. "
            "This fits webhooks, CI pipelines, schedulers, and service-to-service calls "
            "where the task definition changes with every request."
        )

    if scenario.id.startswith("scenario-16-quote-to-cash"):
        story = (
            "This is a Scenario 16 quote-to-cash variant. The same six business roles "
            "(CRM trigger, customer context, SKU discovery, product fit, pricing and legal, "
            "quote generation) appear in every Scenario 16 notebook -- only the orchestration "
            "pattern changes. Compare notebooks 16a-16e to see how the same roles behave "
            "under sequential, concurrent, handoff, group-chat, and magentic coordination."
        )
    elif scenario_uses_a2a(scenario):
        story = (
            "This scenario seats remote partner agents in the council over the A2A protocol. "
            "MCP (scenarios 11-16) connected agents to tools; A2A connects agents to peer "
            "agents owned by other organizations. The orchestration below is the same group "
            "chat used elsewhere -- only where two participants live changes."
        )
    elif scenario_uses_mcp(scenario):
        story = (
            "This is an enterprise scenario grounded by deterministic MCP context tools. "
            "In production those tools are served by a FastMCP stdio subprocess; "
            "this notebook inlines the same functions as plain callables so it runs "
            "without a local package or subprocess."
        )
    else:
        story = (
            "This is a starter scenario. The domain is intentionally lightweight "
            "so the orchestration mechanics are easy to trace before the enterprise "
            "and quote-to-cash notebooks layer in MCP tool calls and richer context."
        )

    anatomy = PATTERN_ANATOMY[scenario.pattern]
    anatomy_rows = "\n".join([
        "| Dimension | Detail |",
        "| --- | --- |",
        "| Control flow | " + anatomy["control_flow"] + " |",
        "| Coordination | " + anatomy["coordination"] + " |",
        "| Output | " + anatomy["output_behavior"] + " |",
        "| Best when | " + anatomy["best_when"] + " |",
    ])

    agent_header = "| Agent | Role | Capabilities |\n| --- | --- | --- |"
    agent_lines = "\n".join(
        "| `" + a.name + "` | " + a.description + " | " + _agent_capability_label(a) + " |"
        for a in scenario.agents
    )
    agent_table = agent_header + "\n" + agent_lines

    pattern_heading = scenario.pattern.replace("-", " ").title()

    return f"""
    ## Pattern: {pattern_heading}

    {concept}

    {best_fit}

    ## API Shape

    {api_note}

    {story}

    ## Pattern Anatomy

    {anatomy_rows}

    ## Instruction-Led LLM Agents

    {agent_table}

    > **Instructor note:** Each row is an LLM-backed agent with role instructions.
    > Most agents rely on instructions alone; enterprise and quote-to-cash agents may
    > also call domain tools for grounded context.
    """


def environment_cells() -> list[dict[str, Any]]:
    config = r'''
    import os

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Domain tools register themselves here; every agent looks up its granted
    # tools by name, so this registry is the one piece of shared runtime state.
    MCP_TOOL_FUNCTIONS: dict[str, object] = {}

    print(f"Ollama target: {OLLAMA_HOST} / {OLLAMA_MODEL}")
    '''

    styling = r'''
    from IPython.display import HTML, Markdown, display


    _AGENT_COLORS = ("#3868c8", "#b0530f", "#2f7d4f", "#7d3f98", "#a3374b", "#0f7d8a", "#8a6d0f", "#54596b")

    _APTOS_STYLE = """
    <style>
    :root { --jp-content-font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif; }
    .jp-RenderedHTMLCommon, .jp-RenderedMarkdown, .rendered_html, .jp-OutputArea-output {
        font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif;
        line-height: 1.55;
    }
    .jp-RenderedHTMLCommon h1, .jp-RenderedHTMLCommon h2, .jp-RenderedHTMLCommon h3 {
        font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    .maf-callout {
        border-left: 4px solid #3868c8; border-radius: 6px; padding: 0.6em 0.9em;
        margin: 0.6em 0; background: rgba(56, 104, 200, 0.08);
    }
    .maf-roster { display: flex; flex-wrap: wrap; gap: 0.6em; margin: 0.4em 0; }
    .maf-card {
        border: 1px solid rgba(128, 128, 128, 0.35); border-radius: 8px;
        padding: 0.55em 0.8em; min-width: 14em; max-width: 24em; flex: 1;
    }
    .maf-card b { display: block; margin-bottom: 0.15em; }
    .maf-card small { opacity: 0.75; }
    .maf-chip {
        display: inline-block; border-radius: 999px; padding: 0 0.6em; margin: 0.2em 0.2em 0 0;
        font-size: 0.78em; border: 1px solid rgba(128, 128, 128, 0.4);
    }
    .maf-turn {
        border-left: 4px solid var(--maf-agent, #54596b); border-radius: 6px;
        padding: 0.45em 0.8em; margin: 0.45em 0; background: rgba(128, 128, 128, 0.07);
        white-space: pre-wrap;
    }
    .maf-turn b { color: var(--maf-agent, inherit); }
    .maf-turn-label {
        border-left: 4px solid var(--maf-agent, #54596b); border-radius: 6px;
        padding: 0.3em 0.7em; margin: 0.7em 0 0.15em; background: rgba(128, 128, 128, 0.09);
    }
    .maf-turn-label b { color: var(--maf-agent, inherit); }
    </style>
    """


    def apply_notebook_style() -> str:
        display(HTML(_APTOS_STYLE))
        return _APTOS_STYLE


    apply_notebook_style()
    '''

    render_helpers = r'''
    import re as _re


    def _escape_html(value) -> str:
        import html as _html

        return _html.escape(str(value))


    def agent_color(name: str) -> str:
        """Deterministic per-agent accent color, stable across cells and runs."""

        return _AGENT_COLORS[sum(ord(ch) for ch in name) % len(_AGENT_COLORS)]


    def render_callout(text: str) -> None:
        display(HTML("<div class='maf-callout'>" + _escape_html(text) + "</div>"))


    def render_roster(scenario) -> None:
        """Render the agent roster as color-accented cards with tool chips."""

        cards = []
        for spec in scenario.agents:
            chips = "".join(
                "<span class='maf-chip'>" + _escape_html(tool) + "</span>" for tool in spec.mcp_tools
            ) or "<span class='maf-chip'>instructions only</span>"
            cards.append(
                "<div class='maf-card' style='border-top: 3px solid " + agent_color(spec.name) + "'>"
                + "<b>" + _escape_html(spec.name) + "</b>"
                + "<small>" + _escape_html(spec.description) + "</small>"
                + "<div>" + chips + "</div></div>"
            )
        display(HTML("<div class='maf-roster'>" + "".join(cards) + "</div>"))


    _TURN_LABEL = _re.compile(r"^\[([A-Za-z0-9_]+)\]\s*", _re.MULTILINE)


    def render_transcript(text: str) -> None:
        """Render workflow output as color-coded per-agent turns.

        Each turn's body is emitted as a ``text/markdown`` output (via
        ``Markdown``) so Jupyter renders the agent's markdown, while the
        per-agent accent color rides on an HTML label bar above the body.
        """

        pieces = _TURN_LABEL.split(text)
        preamble = pieces[0].strip()
        labeled = list(zip(pieces[1::2], pieces[2::2]))
        if not preamble and not labeled:
            display(Markdown(text))
            return
        if preamble:
            display(Markdown(preamble))
        for label, body in labeled:
            display(HTML(
                "<div class='maf-turn-label' style='--maf-agent: " + agent_color(label) + "'>"
                + "<b>" + _escape_html(label) + "</b></div>"
            ))
            display(Markdown(body.strip()))
    '''

    return (
        teach(
            "Runtime configuration",
            SUPPORT,
            "Reads the Ollama model and host from environment variables so the same notebook runs "
            "against any local setup without edits -- override `OLLAMA_MODEL` or `OLLAMA_HOST` "
            "before this cell to retarget it. It also creates `MCP_TOOL_FUNCTIONS`, the shared "
            "registry that fixture cells populate and `make_agent` later reads to grant tools by "
            "name. Nothing here touches the Agent Framework; this is the notebook's runtime dial.",
            config,
        )
        + teach(
            "Notebook styling",
            SUPPORT,
            "Injects the Aptos-inspired CSS the rendering helpers rely on: roster cards, tool "
            "chips, and the per-agent accent bar that colors each transcript turn. `agent_color` "
            "hashes an agent's name to a stable palette entry, which is why the same agent keeps "
            "the same color across every cell and every run. Pure presentation -- no Agent "
            "Framework surface here.",
            styling,
        )
        + teach(
            "Rendering helpers",
            SUPPORT,
            "`render_roster` draws one accent-colored card per agent listing its granted tools, "
            "and `render_transcript` splits workflow output on `[AgentName]` turn labels, "
            "rendering each turn's body as markdown beneath a colored label bar. This is what "
            "turns raw multi-agent output into the readable, color-coded conversation you see "
            "after the live run. Glue for the notebook, not framework API.",
            render_helpers,
        )
    )


def mcp_markdown(server: str | None) -> str:
    if server == "quote_to_cash_context":
        label = "quote-to-cash context"
    else:
        label = "enterprise context"
    return f"""
    ## MCP Tool Context

    In production, these {label} functions are exposed by a local FastMCP stdio server and attached to
    instruction-led LLM agents with `MCPStdioTool` using per-agent allowed tools. This notebook inlines
    the same domain functions as plain callable tools so it remains standalone.
    """


def enterprise_fixtures_cell() -> str:
    return r'''
    from typing import Any


    _ENTERPRISE_RECORDS: dict[str, dict[str, Any]] = {
        "VENDOR-4471": {
            "type": "vendor",
            "name": "Northwind Analytics",
            "category": "data-platform",
            "annual_cost_usd": 184000,
            "data_classification": "confidential",
            "security_review": "expired",
            "owner": "Procurement",
            "notes": "Requested for the billing analytics rollout; SOC 2 report is 14 months old.",
        },
        "ALERT-2298": {
            "type": "security_alert",
            "name": "Anomalous OAuth token usage",
            "severity": "high",
            "affected_users": 3,
            "affected_endpoints": 2,
            "data_loss_indicators": False,
            "token_rotation_completed": False,
            "owner": "SecOps",
            "notes": "Three service accounts issued tokens from an unrecognized ASN within 9 minutes.",
        },
        "CLAIM-88120": {
            "type": "claim",
            "name": "Water damage exception",
            "amount_usd": 42150,
            "policy_id": "POLICY-PROP-12",
            "fraud_signals": 1,
            "compliance_holds": 0,
            "owner": "Claims",
            "notes": "Exceeds auto-approval threshold and includes one mismatched invoice date.",
        },
        "CLAIM-88121": {
            "type": "claim",
            "name": "Storm damage exception",
            "amount_usd": 58900,
            "policy_id": "POLICY-PROP-12",
            "fraud_signals": 2,
            "compliance_holds": 1,
            "owner": "Claims",
            "notes": "Duplicate invoice numbers plus an active regulatory hold; per POL-CLM-09 the fraud review precedes any payment decision.",
        },
        "POLICY-EX-77": {
            "type": "policy_exception",
            "name": "Temporary data residency waiver",
            "requested_by": "EU Sales",
            "risk_area": "data-residency",
            "duration_days": 90,
            "owner": "Governance",
            "notes": "Requests storing EU lead data in us-east during a vendor migration window.",
        },
        "FACILITY-DC-EAST": {
            "type": "facility",
            "name": "East Regional Data Center",
            "criticality": "tier-1",
            "dependent_services": ["billing", "auth", "exports"],
            "last_drill_days_ago": 410,
            "owner": "Operations",
            "notes": "Primary site for billing and auth; continuity drill is overdue.",
        },
        "FACILITY-DC-WEST": {
            "type": "facility",
            "name": "West Regional Data Center",
            "criticality": "tier-2",
            "dependent_services": ["reporting", "archive"],
            "last_drill_days_ago": 120,
            "owner": "Operations",
            "notes": "Secondary site with a current drill; a contrast case when prioritizing scope.",
        },
        "LOAN-73021": {
            "type": "loan_application",
            "name": "Home purchase mortgage application",
            "amount_usd": 384000,
            "credit_score": 764,
            "dti_ratio": 0.31,
            "ltv_ratio": 0.80,
            "employment_years": 6,
            "owner": "Lending",
            "notes": "Salaried applicant with two years of W-2s on file; a clean pass through every underwriting stage.",
        },
        "LOAN-73022": {
            "type": "loan_application",
            "name": "Home purchase mortgage application (marginal)",
            "amount_usd": 402000,
            "credit_score": 668,
            "dti_ratio": 0.44,
            "ltv_ratio": 0.92,
            "employment_years": 1,
            "owner": "Lending",
            "notes": "Self-employed applicant; DTI and LTV both exceed the POL-LEND-01 referral limits, so manual underwriting and compensating factors are required.",
        },
        "TARGET-ACQ-STELLAR": {
            "type": "acquisition_target",
            "name": "Stellar Metrics Ltd",
            "sector": "SaaS product analytics",
            "arr_usd": 24000000,
            "arr_growth_pct": 38,
            "logo_churn_pct": 9,
            "top_customer_revenue_share": 0.34,
            "open_litigation": 1,
            "soc2_status": "none",
            "owner": "Corporate Development",
            "notes": "Fast grower with one pending patent dispute, no SOC 2, a single-region deployment, and a third of revenue from one customer.",
        },
        "TARGET-ACQ-HARBOR": {
            "type": "acquisition_target",
            "name": "Harbor Data GmbH",
            "sector": "EU data-residency analytics",
            "arr_usd": 11000000,
            "arr_growth_pct": 12,
            "logo_churn_pct": 4,
            "top_customer_revenue_share": 0.11,
            "open_litigation": 0,
            "soc2_status": "current",
            "owner": "Corporate Development",
            "notes": "Slower but clean: current certifications, diversified revenue, and an EU footprint; the contrast case for the diligence lanes.",
        },
        "DISPUTE-90455": {
            "type": "transaction_dispute",
            "name": "Duplicate charge with lost-card report",
            "amount_usd": 1249.99,
            "merchant": "TechnoMart Online",
            "duplicate_posting": True,
            "card_reported_lost": True,
            "cardholder_present": False,
            "days_since_posting": 3,
            "owner": "Card Services",
            "notes": "The same amount posted twice (a merchant-error signal) and the cardholder reported the card lost the same week (a fraud signal); POL-DSP-04 makes fraud review win that tie.",
        },
        "DISPUTE-90456": {
            "type": "transaction_dispute",
            "name": "Subscription billed after cancellation",
            "amount_usd": 29.99,
            "merchant": "StreamBox Media",
            "duplicate_posting": False,
            "card_reported_lost": False,
            "cancellation_confirmed": True,
            "days_since_posting": 12,
            "owner": "Card Services",
            "notes": "A recurring charge posted twelve days after a confirmed cancellation; a clean subscription dispute with no fraud signal.",
        },
        "ADR-2209": {
            "type": "architecture_decision",
            "name": "Customer notification service: build versus buy",
            "annual_buy_cost_usd": 96000,
            "build_estimate_eng_quarters": 2,
            "vendor_sla_pct": 99.9,
            "vendor_data_region": "us-only",
            "platform_team_utilization_pct": 85,
            "owner": "Architecture",
            "notes": "The vendor processes data in the US only while a quarter of customers are in the EU; the build option lands on a platform team already at 85% utilization.",
        },
        "METRIC-CHURN-Q3": {
            "type": "metric_anomaly",
            "name": "Q3 enterprise churn spike",
            "baseline_monthly_churn_pct": 1.8,
            "current_monthly_churn_pct": 4.1,
            "spike_start": "week of Sep 8",
            "support_ticket_trend": "flat",
            "nps_delta": -12,
            "owner": "Customer Success",
            "notes": "Churn more than doubled while support volume stayed flat; the spike overlaps a Sep 1 pricing change and billing migration wave 2, so the cause is genuinely ambiguous.",
        },
        "SEGMENT-ENT-EU": {
            "type": "customer_segment",
            "name": "Enterprise EU segment",
            "account_count": 214,
            "arr_usd": 18600000,
            "renewal_concentration": "Q4-heavy",
            "recent_events": [
                "billing migration wave 2 (Sep 5-12)",
                "new DPA requirement emails",
                "P1 outages on Aug 28 and Sep 9",
            ],
            "owner": "Customer Success",
            "notes": "The segment where the churn spike concentrates; three overlapping candidate causes give an investigation real material to eliminate.",
        },
    }

    _POLICY_CATALOG: tuple[dict[str, Any], ...] = (
        {
            "id": "POL-PROC-01",
            "title": "Vendor Security Review",
            "summary": "Vendors handling confidential data require a security review no older than 12 months before purchase.",
            "keywords": ("vendor", "security", "procurement", "soc2", "review", "purchase"),
        },
        {
            "id": "POL-PROC-02",
            "title": "Spend Authorization Thresholds",
            "summary": "Spend above 100k USD requires budget owner plus finance director approval.",
            "keywords": ("budget", "spend", "procurement", "approval", "finance", "threshold"),
        },
        {
            "id": "POL-PROC-03",
            "title": "Regional Processing Exception",
            "summary": "Vendors may process confidential data in-region for up to 30 days during a migration window with security sign-off, even while the annual review is pending.",
            "keywords": ("vendor", "regional", "migration", "exception", "security", "processing"),
        },
        {
            "id": "POL-SEC-04",
            "title": "Identity Compromise Response",
            "summary": "Suspected token or identity compromise requires credential rotation and session revocation within one hour.",
            "keywords": ("identity", "token", "oauth", "security", "incident", "rotation"),
        },
        {
            "id": "POL-CLM-09",
            "title": "Claim Exception Routing",
            "summary": "Claims above the auto-approval threshold or with any fraud signal route to a specialist before payment.",
            "keywords": ("claim", "exception", "fraud", "payment", "threshold"),
        },
        {
            "id": "POL-GOV-03",
            "title": "Policy Exception Board",
            "summary": "Risk waivers require a documented business need, a compensating control, and a fixed expiry. Maximum waiver duration is 60 days.",
            "keywords": ("policy", "exception", "waiver", "risk", "compliance", "governance", "residency"),
        },
        {
            "id": "POL-BCP-02",
            "title": "Business Continuity Drills",
            "summary": "Tier-1 facilities must complete a continuity drill at least every 365 days.",
            "keywords": ("continuity", "drill", "facility", "tier-1", "operations", "recovery"),
        },
        {
            "id": "POL-LEND-01",
            "title": "Manual Underwriting Referral",
            "summary": "Loan applications with a debt-to-income ratio above 0.43 or a loan-to-value ratio above 0.90 require senior underwriter review and documented compensating factors before pricing.",
            "keywords": ("loan", "underwriting", "dti", "ltv", "credit", "referral", "lending"),
        },
        {
            "id": "POL-MA-02",
            "title": "Due Diligence Gate",
            "summary": "Acquisition recommendations require findings from the finance, legal, technology, and market workstreams; any single red flag blocks a proceed recommendation until a documented mitigation exists.",
            "keywords": ("acquisition", "diligence", "merger", "workstream", "target", "gate"),
        },
        {
            "id": "POL-DSP-04",
            "title": "Dispute Routing and Provisional Credit",
            "summary": "Disputes with any fraud indicator route to fraud review before provisional credit; pure merchant errors receive provisional credit within two business days; every dispute is acknowledged within ten business days.",
            "keywords": ("dispute", "fraud", "chargeback", "credit", "merchant", "routing", "card"),
        },
        {
            "id": "POL-ARCH-07",
            "title": "Build-versus-Buy Review",
            "summary": "Build-versus-buy decisions above 50k USD annual impact require a decision record covering total cost of ownership, security posture, data residency, and an exit strategy.",
            "keywords": ("architecture", "build", "buy", "vendor", "decision", "residency", "review"),
        },
    )

    _PLAYBOOKS: dict[str, list[str]] = {
        "procurement-approval": [
            "Confirm the request scope and the requesting business owner.",
            "Validate budget authority against the spend threshold policy.",
            "Confirm the vendor security review is current.",
            "Capture legal and data-protection terms that must be in the contract.",
            "Assemble the approval packet with a clear recommendation.",
        ],
        "security-enrichment": [
            "Pull the alert record and confirm severity.",
            "Enrich the identity dimension.",
            "Enrich the endpoint dimension.",
            "Enrich the network dimension.",
            "Assess data-loss indicators and assemble the incident summary.",
        ],
        "claims-exception": [
            "Normalize the claim and identify why it is an exception.",
            "Check the amount against the auto-approval threshold.",
            "Evaluate fraud signals and compliance holds.",
            "Route to the correct specialist.",
            "Draft the customer communication.",
        ],
        "policy-exception-board": [
            "State the requested exception and the affected policy.",
            "Assess the introduced risk.",
            "Document the business need and urgency.",
            "Define a compensating control and expiry date.",
            "Record the board recommendation.",
        ],
        "continuity-drill": [
            "Confirm the facility, criticality, and dependent services.",
            "Plan the drill scope and participants.",
            "Define IT failover and recovery objectives.",
            "Define communications and stakeholder updates.",
            "Define finance and operations contingencies.",
        ],
        "loan-origination": [
            "Normalize the application and confirm required documents.",
            "Pull credit and flag scores below the referral threshold.",
            "Verify income and recompute the debt-to-income ratio.",
            "Price the risk tier or refer for manual underwriting per policy.",
            "Assemble the offer packet with conditions and disclosures.",
        ],
        "due-diligence": [
            "Confirm the target profile and the deal thesis.",
            "Run finance, legal, technology, and market workstreams in parallel.",
            "Collect red flags and quantify each one.",
            "Check every red flag for a documented mitigation.",
            "Synthesize a proceed, renegotiate, or walk-away recommendation.",
        ],
        "dispute-resolution": [
            "Capture the dispute, the transaction, and the customer's account of events.",
            "Screen for fraud indicators before any credit decision.",
            "Route to the owning specialist based on the dominant signal.",
            "Resolve per policy and record the provisional credit decision.",
            "Send the customer the outcome and the regulatory-clock status.",
        ],
        "architecture-review": [
            "State the decision, the options, and the deadline.",
            "Score total cost of ownership for each option.",
            "Assess security posture and data residency for each option.",
            "Document the exit strategy for the preferred option.",
            "Record the board's decision with dissents and conditions.",
        ],
        "churn-investigation": [
            "Quantify the anomaly against baseline and segment it.",
            "List candidate causes with their supporting evidence.",
            "Assign specialists to confirm or eliminate each candidate.",
            "Reconcile findings and identify the dominant driver.",
            "Recommend remediation and an early-warning metric.",
        ],
    }

    _PRIORITY_TIERS: tuple[tuple[int, str], ...] = (
        (80, "critical"),
        (60, "high"),
        (40, "medium"),
        (0, "low"),
    )



    # Fixture data only -- the tools in the next cell read from these embedded records.
    print("records:  ", ", ".join(sorted(_ENTERPRISE_RECORDS)))
    print("policies: ", ", ".join(policy["id"] for policy in _POLICY_CATALOG))
    print("playbooks:", ", ".join(sorted(_PLAYBOOKS)))
    '''


def enterprise_tools_cell(demo_call: str) -> str:
    template = r'''
    import hashlib
    import json
    from typing import Any


    def _clamp(value: Any, low: int = 1, high: int = 5) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = low
        return max(low, min(high, number))


    def lookup_enterprise_record(record_id: str) -> dict[str, Any]:
        """Look up a single embedded enterprise record by id."""

        key = (record_id or "").strip().upper()
        record = _ENTERPRISE_RECORDS.get(key)
        if record is None:
            return {"found": False, "record_id": record_id, "known_ids": sorted(_ENTERPRISE_RECORDS)}
        return {"found": True, "record_id": key, **record}


    def search_policy(query: str) -> dict[str, Any]:
        """Search the embedded policy catalog with a simple keyword match."""

        terms = [term for term in (query or "").lower().replace(",", " ").split() if term]
        scored: list[tuple[int, dict[str, Any]]] = []
        for policy in _POLICY_CATALOG:
            haystack = " ".join((policy["title"], policy["summary"], " ".join(policy["keywords"]))).lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, policy))
        scored.sort(key=lambda item: (-item[0], item[1]["id"]))
        matches = [
            {"id": policy["id"], "title": policy["title"], "summary": policy["summary"], "match_score": score}
            for score, policy in scored
        ]
        return {"query": query, "match_count": len(matches), "matches": matches}


    def calculate_priority_score(impact: int, urgency: int, scope: int = 1) -> dict[str, Any]:
        """Compute a deterministic 0-100 priority score and tier."""

        impact_v = _clamp(impact)
        urgency_v = _clamp(urgency)
        scope_v = _clamp(scope)
        raw = (impact_v * 8) + (urgency_v * 8) + (scope_v * 4)
        tier = next(name for floor, name in _PRIORITY_TIERS if raw >= floor)
        return {"impact": impact_v, "urgency": urgency_v, "scope": scope_v, "score": raw, "tier": tier}


    def list_playbook_steps(playbook: str) -> dict[str, Any]:
        """Return the ordered steps for an embedded playbook by name."""

        key = (playbook or "").strip().lower().replace("_", "-")
        steps = _PLAYBOOKS.get(key)
        if steps is None:
            return {"found": False, "playbook": playbook, "known_playbooks": sorted(_PLAYBOOKS)}
        return {
            "found": True,
            "playbook": key,
            "step_count": len(steps),
            "steps": [{"order": index, "action": action} for index, action in enumerate(steps, start=1)],
        }


    def create_decision_log_entry(
        subject: str,
        decision: str,
        rationale: str = "",
        owner: str = "unassigned",
    ) -> dict[str, Any]:
        """Return the decision log entry that would be recorded."""

        fingerprint = "|".join((subject or "", decision or "", rationale or "", owner or ""))
        digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
        return {
            "persisted": False,
            "entry_id": f"DLOG-{digest}",
            "subject": subject,
            "decision": decision,
            "rationale": rationale,
            "owner": owner,
        }


    MCP_TOOL_FUNCTIONS.update(
        {
            "lookup_enterprise_record": lookup_enterprise_record,
            "search_policy": search_policy,
            "calculate_priority_score": calculate_priority_score,
            "list_playbook_steps": list_playbook_steps,
            "create_decision_log_entry": create_decision_log_entry,
        }
    )

    # Demo (offline): call one grounded tool directly before any agent exists.
    print(json.dumps(__DEMO_CALL__, indent=2))
    '''
    return template.replace("__DEMO_CALL__", demo_call)


def quote_to_cash_fixtures_cell() -> str:
    return r'''
    from typing import Any


    _QUOTE_TRIGGERS: dict[str, dict[str, Any]] = {
        "OPP-5001": {
            "opportunity_id": "OPP-5001",
            "account_id": "ACC-3300",
            "stage": "Negotiation",
            "quote_ready": True,
            "trigger_conditions": [
                "Opportunity stage is Negotiation or later.",
                "Primary contact and billing account are set.",
                "Budget is confirmed by the customer.",
            ],
            "blocking_conditions": [],
        },
        "OPP-5002": {
            "opportunity_id": "OPP-5002",
            "account_id": "ACC-3301",
            "stage": "Discovery",
            "quote_ready": False,
            "trigger_conditions": ["Opportunity stage is Negotiation or later."],
            "blocking_conditions": [
                "Opportunity is still in Discovery.",
                "No confirmed budget on the opportunity.",
            ],
        },
    }

    _CUSTOMER_PROFILES: dict[str, dict[str, Any]] = {
        "ACC-3300": {
            "account_id": "ACC-3300",
            "customer_name": "Contoso Manufacturing",
            "address": "120 Industrial Way, Aurora, IL 60502, USA",
            "msa_status": "signed",
            "account_status": "active",
            "segment": "enterprise",
            "buying_context": "Expanding plant automation; standardizing on one analytics platform.",
        },
        "ACC-3301": {
            "account_id": "ACC-3301",
            "customer_name": "Fabrikam Logistics",
            "address": "44 Harbor Rd, Tacoma, WA 98402, USA",
            "msa_status": "in_review",
            "account_status": "active",
            "segment": "mid-market",
            "buying_context": "Evaluating route-optimization add-ons for peak season.",
        },
    }

    _CATALOG: tuple[dict[str, Any], ...] = (
        {"sku": "SKU-ANALYTICS-CORE", "name": "Analytics Core Platform", "bundle": "platform", "list_price": 48000, "keywords": ("analytics", "platform", "core")},
        {"sku": "SKU-ANALYTICS-EDGE", "name": "Edge Connector Pack", "bundle": "platform", "list_price": 12000, "keywords": ("analytics", "edge", "connector", "automation")},
        {"sku": "SKU-SUPPORT-PREM", "name": "Premier Support (12 mo)", "bundle": "support", "list_price": 9000, "keywords": ("support", "premier", "service")},
        {"sku": "SKU-ROUTE-OPT", "name": "Route Optimization Add-on", "bundle": "logistics", "list_price": 15000, "keywords": ("route", "optimization", "logistics")},
        {"sku": "SKU-TRAINING-1", "name": "Onboarding & Training", "bundle": "services", "list_price": 6000, "keywords": ("training", "onboarding", "services")},
    )

    _SKU_INDEX = {entry["sku"]: entry for entry in _CATALOG}
    _INCOMPATIBLE_PAIRS = {("SKU-ROUTE-OPT", "SKU-ANALYTICS-EDGE")}
    _UNAVAILABLE_SKUS = {"SKU-TRAINING-1"}

    _LEGAL_TERMS: dict[str, dict[str, Any]] = {
        "enterprise": {
            "segment": "enterprise",
            "risk_level": "medium",
            "clauses": [
                "Net-45 payment terms.",
                "Standard MSA governs; no bespoke indemnity without legal review.",
                "Auto-renewal with 60-day opt-out.",
            ],
            "approvals_required": ["Deal desk", "Legal (if discount > 20%)"],
        },
        "mid-market": {
            "segment": "mid-market",
            "risk_level": "low",
            "clauses": ["Net-30 payment terms.", "Click-through terms acceptable below $50k."],
            "approvals_required": ["Deal desk"],
        },
    }



    # Fixture data only -- the tools in the next cell read from these embedded records.
    print("opportunities:", ", ".join(sorted(_QUOTE_TRIGGERS)))
    print("accounts:     ", ", ".join(sorted(_CUSTOMER_PROFILES)))
    print("catalog SKUs: ", ", ".join(entry["sku"] for entry in _CATALOG))
    '''


def quote_to_cash_tools_cell(demo_call: str) -> str:
    template = r'''
    import hashlib
    import json
    from typing import Any


    def _string_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            pieces = value.replace(";", ",").replace("\n", ",").split(",")
            return [piece.strip() for piece in pieces if piece.strip()]
        try:
            items = iter(value)
        except TypeError:
            text = str(value).strip()
            return [text] if text else []
        flattened: list[str] = []
        for item in items:
            flattened.extend(_string_list(item))
        return flattened


    def crm_get_quote_trigger(opportunity_id: str = "OPP-5001") -> dict[str, Any]:
        """Return CRM trigger state for an opportunity."""

        key = (opportunity_id or "").strip().upper()
        record = _QUOTE_TRIGGERS.get(key)
        if record is None:
            return {"found": False, "opportunity_id": opportunity_id, "known_ids": sorted(_QUOTE_TRIGGERS)}
        return {"found": True, **record}


    def crm_get_customer_profile(account_id: str = "ACC-3300") -> dict[str, Any]:
        """Return the enriched CRM customer profile for an account."""

        key = (account_id or "").strip().upper()
        record = _CUSTOMER_PROFILES.get(key)
        if record is None:
            return {"found": False, "account_id": account_id, "known_ids": sorted(_CUSTOMER_PROFILES)}
        return {"found": True, **record}


    def product_search_catalog(query: str = "analytics platform") -> dict[str, Any]:
        """Search the product/SKU catalog with a simple keyword match."""

        terms = [term for term in (query or "").lower().replace(",", " ").split() if term]
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in _CATALOG:
            haystack = " ".join((entry["name"], entry["bundle"], " ".join(entry["keywords"]))).lower()
            score = sum(1 for term in terms if term in haystack)
            if score or not terms:
                scored.append((score, entry))
        scored.sort(key=lambda item: (-item[0], item[1]["sku"]))
        matches = [
            {"sku": e["sku"], "name": e["name"], "bundle": e["bundle"], "list_price": e["list_price"], "match_score": s}
            for s, e in scored
        ]
        return {"query": query, "match_count": len(matches), "matches": matches}


    def product_validate_skus(skus: str = "") -> dict[str, Any]:
        """Validate SKU compatibility, availability, and completeness."""

        requested = _string_list(skus) or [entry["sku"] for entry in _CATALOG[:2]]
        requested_set = {sku.strip().upper() for sku in requested}
        validated: list[dict[str, Any]] = []
        for sku in requested:
            key = sku.strip().upper()
            known = key in _SKU_INDEX
            available = known and key not in _UNAVAILABLE_SKUS
            compatible = not any(
                {key, other} == set(pair) for pair in _INCOMPATIBLE_PAIRS for other in requested_set
            )
            validated.append(
                {
                    "sku": key,
                    "known": known,
                    "compatible": compatible,
                    "available": available,
                    "complete": bool(known and available and compatible),
                }
            )
        all_valid = bool(validated) and all(item["complete"] for item in validated)
        return {"requested": requested, "validated": validated, "all_valid": all_valid}


    def pricing_calculate_quote(skus: str = "", discount_pct: float = 0.0) -> dict[str, Any]:
        """Calculate quote pricing for a set of SKUs."""

        requested = _string_list(skus) or [entry["sku"] for entry in _CATALOG[:2]]
        line_items: list[dict[str, Any]] = []
        subtotal = 0
        for sku in requested:
            key = sku.strip().upper()
            entry = _SKU_INDEX.get(key)
            price = int(entry["list_price"]) if entry else 0
            subtotal += price
            line_items.append({"sku": key, "list_price": price, "in_catalog": entry is not None})
        try:
            pct = float(discount_pct)
        except (TypeError, ValueError):
            pct = 0.0
        pct = max(0.0, min(40.0, pct))
        discount = round(subtotal * pct / 100.0, 2)
        total = round(subtotal - discount, 2)
        return {
            "currency": "USD",
            "line_items": line_items,
            "subtotal": subtotal,
            "discount_pct": pct,
            "discount": discount,
            "total": total,
        }


    def legal_evaluate_terms(segment: str = "enterprise", discount_pct: float = 0.0) -> dict[str, Any]:
        """Return legal/contract terms and required approvals for a segment."""

        key = (segment or "").strip().lower()
        terms = _LEGAL_TERMS.get(key, _LEGAL_TERMS["enterprise"])
        try:
            pct = float(discount_pct)
        except (TypeError, ValueError):
            pct = 0.0
        approvals = list(terms["approvals_required"])
        if pct > 20 and "Legal review" not in approvals:
            approvals.append("Legal review (discount over 20%)")
        return {
            "segment": terms["segment"],
            "risk_level": terms["risk_level"],
            "clauses": list(terms["clauses"]),
            "approvals_required": approvals,
        }


    def quote_format_package(
        customer_name: str = "Contoso Manufacturing",
        total: float = 0.0,
        skus: str = "",
    ) -> dict[str, Any]:
        """Format the final customer-ready quote package."""

        requested = _string_list(skus)
        fingerprint = "|".join([customer_name, ",".join(requested), f"{float(total or 0.0):.2f}"])
        digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:8]
        return {
            "quote_id": f"Q2C-{digest}",
            "format": "pdf",
            "customer_name": customer_name,
            "total": round(float(total or 0.0), 2),
            "skus": [sku.strip().upper() for sku in requested],
            "sections": ["Cover", "Customer & MSA", "Line Items & Pricing", "Terms & Conditions", "Signature"],
            "customer_ready": True,
        }


    MCP_TOOL_FUNCTIONS.update(
        {
            "crm_get_quote_trigger": crm_get_quote_trigger,
            "crm_get_customer_profile": crm_get_customer_profile,
            "product_search_catalog": product_search_catalog,
            "product_validate_skus": product_validate_skus,
            "pricing_calculate_quote": pricing_calculate_quote,
            "legal_evaluate_terms": legal_evaluate_terms,
            "quote_format_package": quote_format_package,
        }
    )

    # Demo (offline): call one grounded tool directly before any agent exists.
    print(json.dumps(__DEMO_CALL__, indent=2))
    '''
    return template.replace("__DEMO_CALL__", demo_call)


def agent_factory_cells() -> list[dict[str, Any]]:
    config = r'''
    from dataclasses import dataclass
    from typing import Any

    from agent_framework.ollama import OllamaChatClient


    DEFAULT_OLLAMA_TEMPERATURE = 0.0
    DEFAULT_OLLAMA_NUM_CTX = 8192
    DEFAULT_OLLAMA_KEEP_ALIVE = "10m"
    DEFAULT_OLLAMA_THINK = False

    # Ollama's chat endpoint rejects a few OpenAI-style options; we strip these later.
    _UNSUPPORTED_OLLAMA_CHAT_OPTIONS = {
        "allow_multiple_tool_calls",
        "conversation_id",
        "logit_bias",
        "metadata",
        "store",
        "user",
    }


    @dataclass(frozen=True)
    class OllamaAgentConfig:
        model: str
        host: str
        temperature: float
        num_ctx: int
        max_tokens: int
        keep_alive: str
        think: bool

        def default_options(self) -> dict[str, Any]:
            return {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "max_tokens": self.max_tokens,
                "keep_alive": self.keep_alive,
                "think": self.think,
            }


    def parse_env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None or value.strip() == "":
            return default
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"{name} must be true or false.")


    def build_ollama_config(
        *,
        model: str | None = None,
        host: str | None = None,
        temperature: float | None = None,
        num_ctx: int | None = None,
        max_tokens: int | None = None,
        keep_alive: str | None = None,
        think: bool | None = None,
    ) -> OllamaAgentConfig:
        return OllamaAgentConfig(
            model=model or os.getenv("OLLAMA_MODEL") or "gemma4:12b",
            host=host or os.getenv("OLLAMA_HOST") or "http://localhost:11434",
            temperature=temperature
            if temperature is not None
            else float(os.getenv("OLLAMA_TEMPERATURE", str(DEFAULT_OLLAMA_TEMPERATURE))),
            num_ctx=num_ctx if num_ctx is not None else int(os.getenv("OLLAMA_NUM_CTX", str(DEFAULT_OLLAMA_NUM_CTX))),
            max_tokens=max_tokens if max_tokens is not None else int(os.getenv("OLLAMA_MAX_TOKENS", "1000")),
            keep_alive=keep_alive or os.getenv("OLLAMA_KEEP_ALIVE") or DEFAULT_OLLAMA_KEEP_ALIVE,
            think=think if think is not None else parse_env_bool("OLLAMA_THINK", DEFAULT_OLLAMA_THINK),
        )
    '''

    client_subclass = r'''
    class ScenarioOllamaChatClient(OllamaChatClient):
        """OllamaChatClient that drops chat options the local Ollama server rejects."""

        def _prepare_options(self, messages: Any, options: Any) -> dict[str, Any]:
            filtered = {
                key: value
                for key, value in dict(options).items()
                if key not in _UNSUPPORTED_OLLAMA_CHAT_OPTIONS
            }
            return super()._prepare_options(messages, filtered)
    '''

    make_agent = r'''
    def make_agent(spec: Any, *, config: OllamaAgentConfig | None = None) -> Any:
        if spec.a2a_url:
            from agent_framework.a2a import A2AAgent

            url = spec.a2a_url
            if not url.startswith("http"):
                url = os.getenv("A2A_PARTNER_BASE_URL", "http://localhost:8765").rstrip("/") + url
            return A2AAgent(name=spec.name, description=spec.description, url=url)

        resolved = config or build_ollama_config()
        instructions = f"You are {spec.name}. {spec.instructions}"
        tools = tools_for_agent(spec)
        return ScenarioOllamaChatClient(host=resolved.host, model=resolved.model).as_agent(
            name=spec.name,
            description=spec.description,
            instructions=instructions,
            tools=tools or None,
            default_options=resolved.default_options(),
            require_per_service_call_history_persistence=True,
        )


    print("Agent factory ready: make_agent(spec) creates an instruction-led Ollama agent "
          "with its granted tools attached.")
    '''

    return (
        teach(
            "Ollama configuration",
            SUPPORT,
            "A frozen `OllamaAgentConfig` dataclass captures everything one agent's chat client "
            "needs -- model, host, temperature, context window, the scenario's token budget, "
            "keep-alive, and the think flag -- with environment variables as the override "
            "channel. Freezing it guarantees every agent in a run shares identical runtime "
            "settings. Local-runtime plumbing, independent of any Agent Framework class.",
            config,
        )
        + teach(
            "Chat-client shim",
            SUPPORT,
            "A thin `OllamaChatClient` subclass that strips chat options the local Ollama server "
            "would reject before each request goes out. Adapters like this are common at the edge "
            "between a framework and a specific model server: the framework speaks a superset, "
            "the server accepts a subset, and the shim reconciles them without touching any agent "
            "code.",
            client_subclass,
        )
        + teach(
            "make_agent",
            PRIMITIVE,
            "The factory this whole repo pivots on: `client.as_agent(...)` combines a chat "
            "client, the spec's role instructions (prefixed with the agent's name), and any "
            "granted tools into a runnable agent -- or returns an `A2AAgent` when the spec points "
            "at a remote peer. Every orchestration pattern downstream consumes agents built "
            "exactly here, which is why instructions and tool grants live in the scenario spec "
            "rather than in pattern code. This is the Agent Framework's core agent-construction "
            "call.",
            make_agent,
        )
    )


def scenario_cells(project: dict[str, str], data: dict[str, Any]) -> list[dict[str, Any]]:
    sample_attr = project["sample_attr"]
    scenario_json = textwrap.indent(json.dumps(data, indent=2), "    ")
    sample_prompt = (
        "SAMPLE_PROMPT = SCENARIO.sample_input"
        if sample_attr == "sample_input"
        else "SAMPLE_PROMPT = build_invocation_prompt(INVOCATION_PAYLOAD)"
    )
    payload = (
        '    RESPONSES_PAYLOAD = {"input": SCENARIO.sample_input, "stream": False}'
        if sample_attr == "sample_input"
        else textwrap.indent(
            textwrap.dedent(
                '''
            INVOCATION_PAYLOAD = {
                "scenario": SCENARIO.id,
                "pattern": SCENARIO.pattern,
                "task": SCENARIO.sample_task,
                "subject": "notebook sample",
                "artifacts": [],
                "constraints": [],
                "stream": False,
            }
            '''
            ).strip(),
            "    ",
        )
    )
    invocation_prompt = (
        ""
        if sample_attr == "sample_input"
        else textwrap.indent(
            textwrap.dedent(
                r'''


                def build_invocation_prompt(payload: dict[str, object]) -> str:
                    artifacts = "\n".join(f"- {item}" for item in payload.get("artifacts", [])) or "- No artifacts supplied."
                    constraints = "\n".join(f"- {item}" for item in payload.get("constraints", [])) or "- No explicit constraints."
                    return (
                        f"Scenario: {payload['scenario']} - {SCENARIO.title}\n"
                        f"Pattern: {payload['pattern']}\n"
                        f"Learning goal: {SCENARIO.learning_goal}\n"
                        f"Subject: {payload['subject']}\n"
                        f"Task: {payload['task']}\n\n"
                        f"Artifacts:\n{artifacts}\n\n"
                        f"Constraints:\n{constraints}\n\n"
                        "Session context:\nNo prior turns for this session.\n\n"
                        "Return actionable findings. Do not claim to have inspected artifacts beyond the provided names and context."
                    )
                '''
            ).strip("\n"),
            "    ",
        )
    )
    schema = f'''
    from dataclasses import dataclass
    from typing import Any, Sequence


    @dataclass(frozen=True)
    class AgentSpec:
        name: str
        description: str
        instructions: str
        mcp_tools: tuple[str, ...] = ()
        mcp_server: str = "enterprise_context"
        route_keywords: tuple[str, ...] = ()
        a2a_url: str | None = None


    @dataclass(frozen=True)
    class ScenarioSpec:
        id: str
        pattern: str
        title: str
        learning_goal: str
        when_to_use: str
        {sample_attr}: str
        agents: tuple[AgentSpec, ...]
        max_tokens: int
        handoff_finisher: str | None = None
        concurrent_synthesizer: str | None = None
        termination_phrases: tuple[str, ...] = ()
    '''

    hydrate = f'''
    import json


    SCENARIO_DATA = json.loads(
        r"""
{scenario_json}
        """
    )
    AGENTS = tuple(
        AgentSpec(
            name=item["name"],
            description=item["description"],
            instructions=item["instructions"],
            mcp_tools=tuple(item.get("mcp_tools", [])),
            mcp_server=item.get("mcp_server", "enterprise_context"),
            route_keywords=tuple(item.get("route_keywords", [])),
            a2a_url=item.get("a2a_url"),
        )
        for item in SCENARIO_DATA["agents"]
    )
    SCENARIO = ScenarioSpec(
        id=SCENARIO_DATA["id"],
        pattern=SCENARIO_DATA["pattern"],
        title=SCENARIO_DATA["title"],
        learning_goal=SCENARIO_DATA["learning_goal"],
        when_to_use=SCENARIO_DATA["when_to_use"],
        {sample_attr}=SCENARIO_DATA["{sample_attr}"],
        agents=AGENTS,
        max_tokens=SCENARIO_DATA["max_tokens"],
        handoff_finisher=SCENARIO_DATA.get("handoff_finisher"),
        concurrent_synthesizer=SCENARIO_DATA.get("concurrent_synthesizer"),
        termination_phrases=tuple(SCENARIO_DATA.get("termination_phrases", [])),
    )

    print(f"Loaded {{SCENARIO.title}} with {{len(SCENARIO.agents)}} agents.")
    '''

    helpers = f'''
    def tools_for_agent(spec: AgentSpec) -> list[object]:
        tools: list[object] = []
        for tool_name in spec.mcp_tools:
            try:
                tools.append(MCP_TOOL_FUNCTIONS[tool_name])
            except KeyError as exc:
                raise ValueError(f"Missing inlined tool '{{tool_name}}' for {{spec.name}}.") from exc
        return tools


    def scenario_summary(scenario: ScenarioSpec) -> dict[str, str]:
        return {{
            "id": scenario.id,
            "title": scenario.title,
            "pattern": scenario.pattern,
            "learning_goal": scenario.learning_goal,
            "when_to_use": scenario.when_to_use,
            "max_tokens": str(scenario.max_tokens),
            "sample": getattr(scenario, "{sample_attr}"),
        }}


    def agent_capability_map(scenario: ScenarioSpec) -> list[dict[str, Any]]:
        return [
            {{
                "agent": spec.name,
                "description": spec.description,
                "instructions": spec.instructions,
                "mcp_tools": list(spec.mcp_tools),
                "mcp_server": spec.mcp_server if spec.mcp_tools else None,
            }}
            for spec in scenario.agents
        ]


    def mcp_tool_context(scenario: ScenarioSpec) -> dict[str, Any]:
        tools_by_agent = {{spec.name: list(spec.mcp_tools) for spec in scenario.agents if spec.mcp_tools}}
        all_tools_used = sorted({{tool for spec in scenario.agents for tool in spec.mcp_tools}})
        return {{
            "uses_mcp": bool(all_tools_used),
            "tools_by_agent": tools_by_agent,
            "all_tools_used": all_tools_used,
        }}
{invocation_prompt}
    '''

    finalize = f'''
    import json


    MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", str(SCENARIO.max_tokens)))
{payload}
    {sample_prompt}

    render_roster(SCENARIO)
    print(json.dumps(scenario_summary(SCENARIO), indent=2))
    print(json.dumps(agent_capability_map(SCENARIO), indent=2))
    if mcp_tool_context(SCENARIO)["uses_mcp"]:
        print(json.dumps(mcp_tool_context(SCENARIO), indent=2))
    '''

    return (
        teach(
            "Scenario schema",
            SUPPORT,
            "Plain frozen dataclasses -- `AgentSpec` and `ScenarioSpec` -- that mirror the "
            "embedded scenario JSON: identity, pattern, roster, token budget, and the pattern- "
            "specific fields (`handoff_finisher`, `concurrent_synthesizer`, "
            "`termination_phrases`). They are deliberately not framework types: keeping the "
            "scenario contract in plain data is what lets the same spec drive five different "
            "orchestrations and both API shapes.",
            schema,
        )
        + teach(
            "Load the scenario",
            SUPPORT,
            "Hydrates the embedded JSON into the `SCENARIO` object every later cell reads -- the "
            "roster the agent factory builds from, the sample prompt the live run sends, and the "
            "budget the config uses. Change a field here (an instruction, a route keyword, the "
            "budget) and rerun the downstream cells to see how behavior shifts. Data plumbing, no "
            "Agent Framework surface.",
            hydrate,
        )
        + teach(
            "Inspection helpers",
            SUPPORT,
            "`agent_capability_map` summarizes who can do what, `mcp_tool_context` reports which "
            "domain tools exist, and `tools_for_agent` resolves an agent's granted tool names to "
            "the actual callables `make_agent` will attach. Inspecting the roster this way before "
            "running is a habit worth keeping: most orchestration surprises trace back to an "
            "agent having more, fewer, or different tools than you assumed.",
            helpers,
        )
        + teach(
            "Sample prompt and budget",
            SUPPORT,
            "Pins the two run-defining inputs: `MAX_TOKENS`, the per-turn generation budget (this "
            "scenario's recommended value unless `OLLAMA_MAX_TOKENS` overrides it), and "
            "`SAMPLE_PROMPT`, the exact text the live run will dispatch. It then renders the "
            "roster so you can see the team -- and each agent's accent color -- before any "
            "orchestration happens. Budgets matter locally: too low truncates an agent mid- "
            "thought, too high slows every turn.",
            finalize,
        )
    )


def plumbing_cells() -> list[dict[str, Any]]:
    imports_and_messages = r'''
    import re
    from typing import Any, Never

    from agent_framework import (
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        Executor,
        Message,
        WorkflowBuilder,
        WorkflowContext,
        handler,
    )


    # State keys shared across executors: the running transcript, and the stopwords
    # the handoff router strips when it derives routing keywords from agent names.
    _TRANSCRIPT_KEY = "transcript"
    _STOPWORDS = {"agent", "specialist", "the", "and", "for", "with", "that", "from", "into"}


    def make_request(text: str) -> AgentExecutorRequest:
        return AgentExecutorRequest(messages=[Message(role="user", contents=[text])])


    def response_text(response: AgentExecutorResponse) -> str:
        agent_response = getattr(response, "agent_response", None)
        return (getattr(agent_response, "text", None) or "").strip()
    '''

    transcript_state = r'''
    def _append_transcript(ctx: WorkflowContext[Any], author: str, text: str) -> list[str]:
        transcript = list(ctx.get_state(_TRANSCRIPT_KEY) or [])
        transcript.append(f"[{author}] {text}")
        ctx.set_state(_TRANSCRIPT_KEY, transcript)
        return transcript
    '''

    dispatch_executor = r'''
    class PromptDispatchExecutor(Executor):
        @handler
        async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            ctx.set_state("prompt", prompt)
            ctx.set_state(_TRANSCRIPT_KEY, [])
            await ctx.send_message(make_request(prompt))
    '''

    agent_nodes = r'''
    def _slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


    def _agents_for(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> list[Any]:
        return [make_agent(spec, config=config) for spec in scenario.agents]


    def _agent_executor(spec_index: int, scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> AgentExecutor:
        spec = scenario.agents[spec_index]
        return AgentExecutor(make_agent(spec, config=config), id=_slug(spec.name))


    print("Workflow plumbing ready: dispatch executor, shared transcript state, and "
          "request/response helpers.")
    '''

    return (
        teach(
            "Framework imports and message helpers",
            PRIMITIVE,
            "Imports the workflow surface every pattern in this repo builds on -- `Executor`, "
            "`WorkflowBuilder`, `WorkflowContext`, `AgentExecutor`, and the `@handler` decorator "
            "-- plus `make_request` and `response_text`, two helpers that wrap plain text into an "
            "`AgentExecutorRequest` and pull it back out of a response. Messages are the typed "
            "boundary between workflow nodes: everything an agent receives or returns passes "
            "through these shapes.",
            imports_and_messages,
        )
        + teach(
            "Transcript state",
            SUPPORT,
            "A helper that appends a `[AgentName] text` line to the shared transcript stored in "
            "workflow state via `ctx.get_state`/`ctx.set_state`. Keeping the transcript in state "
            "-- rather than inside any single executor -- is what lets gates, routers, and output "
            "executors all read the same running history. Bookkeeping the executors reuse, not "
            "framework API itself.",
            transcript_state,
        )
        + teach(
            "Your first executor",
            PRIMITIVE,
            "`PromptDispatchExecutor` is the minimal custom executor: subclass `Executor`, mark "
            "an async method with `@handler`, and the framework routes matching messages to it. "
            "This one seeds the prompt and an empty transcript into state, then `send_message`s "
            "the first request -- the entry node of every graph in this repo. The handler "
            "signature (input type plus `WorkflowContext[OutputType]`) is how the framework knows "
            "what a node consumes and emits.",
            dispatch_executor,
        )
        + teach(
            "Agents as workflow nodes",
            PRIMITIVE,
            "`_agent_executor` wraps a factory-built agent in an `AgentExecutor`, giving it a "
            "graph id and making it addressable as a workflow node -- the bridge between the "
            "agent world (instructions, tools, chat client) and the workflow world (edges, "
            "handlers, state). The slugified id matters more than it looks: the handoff router "
            "targets specialists by exactly these ids.",
            agent_nodes,
        )
    )


_PATTERN_MACHINERY = {
    'sequential': [
        (
            "StageGateExecutor: carry the transcript forward",
            PRIMITIVE,
            "The sequential pattern's engine. After each stage responds, this gate appends the "
            "stage's output to the shared transcript and sends the next agent a fresh request "
            "containing the original prompt plus all accumulated work -- so stage N+1 sees "
            "everything stages 1 through N produced, not just the last message. The explicit 'do "
            "not repeat the earlier stages' instruction is a small but real guard against agents "
            "re-answering the whole task.",
            r'''
    class StageGateExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(transcript)
            await ctx.send_message(
                make_request(
                    f"Original request:\n{prompt}\n\nWork so far:\n{carried}\n\n"
                    "Add your stage's contribution; do not repeat the earlier stages."
                )
            )
    ''',
        ),
        (
            "SequentialOutputExecutor: yield the final transcript",
            PRIMITIVE,
            "The terminal node: instead of forwarding another request, its handler calls "
            "`ctx.yield_output(...)` with the joined transcript, and that value becomes the "
            "workflow's result. Every pattern in this repo ends at an executor that yields rather "
            "than sends -- yielding is how a graph declares 'this is the answer'.",
            r'''
    class SequentialOutputExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            await ctx.yield_output("\n\n".join(transcript))
    ''',
        ),
        (
            "Preview the stage handoff",
            SUPPORT,
            "An offline sanity check -- no model call -- that prints the exact prompt one stage "
            "gate hands the next, using stand-in findings. Read it once before the live run: when "
            "a later stage misbehaves, the first question is always 'what did it actually "
            "receive?', and this cell shows you precisely that shape.",
            r'''
    # Demo (offline): the exact prompt a stage gate hands to the next stage.
    _demo_transcript = [
        f"[{SCENARIO.agents[0].name}] First-stage findings would appear here.",
        f"[{SCENARIO.agents[1].name}] Second-stage findings build on them.",
    ]
    print("Original request:\n" + SAMPLE_PROMPT + "\n\nWork so far:\n" + "\n".join(_demo_transcript))
    ''',
        ),
    ],
    'concurrent': [
        (
            "Attribute each parallel result",
            SUPPORT,
            "Fan-in delivers the parallel responses in nondeterministic completion order, so this "
            "helper pairs each response back to its agent by executor id, with a positional "
            "fallback. Without this labelling the combined output would be anonymous paragraphs; "
            "with it, every finding stays attributable to its lane -- which is most of the value "
            "of a concurrent review.",
            r'''
    def _labelled_responses(responses: list, agent_names: list) -> list:
        """Pair fan-in responses with agent names by executor_id, position fallback."""

        names_by_slug = {_slug(name): name for name in agent_names}
        labelled = []
        for index, response in enumerate(responses):
            name = names_by_slug.get(getattr(response, "executor_id", None) or "")
            if name is None:
                name = agent_names[index] if index < len(agent_names) else f"agent{index + 1}"
            labelled.append((name, response_text(response)))
        return labelled
    ''',
        ),
        (
            "ConcurrentAggregatorExecutor: fan-in and combine",
            PRIMITIVE,
            "The fan-in `Executor`. Note the handler's input type -- "
            "`list[AgentExecutorResponse]` -- the framework collects every parallel lane's "
            "response and delivers them in a single call, which is what makes this node a fan-in "
            "rather than an ordinary edge. It labels the findings and `yield_output`s the "
            "combination; this is the terminal node when the scenario declares no synthesizer.",
            r'''
    class ConcurrentAggregatorExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names

        @handler
        async def aggregate(self, responses: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]) -> None:
            labelled = _labelled_responses(responses, self._agent_names)
            await ctx.yield_output("\n\n".join(f"[{name}]\n{text}" for name, text in labelled))
    ''',
        ),
        (
            "ConcurrentSynthesisGateExecutor: forward to a synthesizer",
            PRIMITIVE,
            "When the scenario names a synthesizer, this fan-in gate takes the aggregator's "
            "place: it labels the parallel findings into the transcript and forwards them onward "
            "as a new request so the synthesis agent can reconcile them. That ordering is the "
            "point -- the agent that combines the perspectives actually sees them, instead of "
            "summarizing from its own imagination.",
            r'''
    class ConcurrentSynthesisGateExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names

        @handler
        async def gate(self, responses: list[AgentExecutorResponse], ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            for name, text in _labelled_responses(responses, self._agent_names):
                _append_transcript(ctx, name, text)
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(ctx.get_state(_TRANSCRIPT_KEY) or [])
            await ctx.send_message(
                make_request(
                    f"You are the synthesis stage.\nOriginal request:\n{prompt}\n\n"
                    f"Independent specialist findings:\n{carried}\n\n"
                    "Combine these findings into the final deliverable."
                )
            )
    ''',
        ),
        (
            "Terminal output executor",
            PRIMITIVE,
            "The terminal `Executor` that yields the joined transcript. It exists only on the "
            "synthesizer path -- after the synthesis gate and the synthesis agent -- because on "
            "the plain path the aggregator itself terminates the workflow. Two closing shapes, "
            "one pattern: check which one your scenario built.",
            r'''
    class SequentialOutputExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            await ctx.yield_output("\n\n".join(transcript))
    ''',
        ),
        (
            "Preview fan-in labelling",
            SUPPORT,
            "An offline check -- no model call -- of how each parallel lane's finding will be "
            "labelled before aggregation. The labels come straight from the roster, so if a lane "
            "seems to vanish from live output, compare its name here against the executor ids "
            "first.",
            r'''
    # Demo (offline): how fan-in labels each parallel finding before aggregation.
    _parallel = [spec.name for spec in SCENARIO.agents if spec.name != SCENARIO.concurrent_synthesizer][:3]
    print("\n\n".join(f"[{name}]\n{name} would report its independent finding here." for name in _parallel))
    ''',
        ),
    ],
    'handoff': [
        (
            "Parse the ROUTE directive",
            SUPPORT,
            "A regex and a slugifier that read the `ROUTE: <AgentName>` line the triage agent was "
            "instructed to end with. Notice how forgiving the pattern is -- case-insensitive, "
            "tolerant of spacing -- because models format directives inconsistently; and notice "
            "what it does not do: validate. Deciding whether the named route is allowed belongs "
            "to the router, not the parser.",
            r'''
    _ROUTE_DIRECTIVE = re.compile(r"route\s*:\s*([A-Za-z][A-Za-z0-9 _-]*)", re.IGNORECASE)


    def _route_slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    ''',
        ),
        (
            "HandoffRouterExecutor: validate the model's choice",
            PRIMITIVE,
            "The heart of the pattern: the model suggests, code decides. The plain methods are "
            "testable without a workflow -- `directed` honors a valid ROUTE line, `decide` falls "
            "back to scoring each specialist's keywords against the triage text and records which "
            "mechanism won -- and the `@handler` commits the choice to state and `send_message`s "
            "the chosen specialist via `target_id`. That `target_id` argument is the framework "
            "primitive that makes dynamic routing possible: one node, many possible next hops.",
            r'''
    class HandoffRouterExecutor(Executor):
        def __init__(
            self,
            id: str,
            *,
            routes: dict[str, tuple[str, ...]],
            default_route: str,
            display_names: dict[str, str] | None = None,
        ) -> None:
            super().__init__(id=id)
            self._routes = routes
            self._default_route = default_route
            self._display_names = display_names or {}

        def directed(self, text: str) -> str | None:
            for match in reversed(_ROUTE_DIRECTIVE.findall(text)):
                slug = _route_slug(match)
                if slug in self._routes:
                    return slug
            return None

        def decide(self, text: str) -> tuple[str, str]:
            directed = self.directed(text)
            if directed is not None:
                return directed, "model-directive"
            lowered = text.lower()
            best_route, best_hits = self._default_route, 0
            for route, keywords in self._routes.items():
                hits = sum(1 for keyword in keywords if keyword in lowered)
                if hits > best_hits:
                    best_route, best_hits = route, hits
            return best_route, "keyword-score"

        def choose(self, text: str) -> str:
            return self.decide(text)[0]

        @handler
        async def route(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            triage_text = response_text(response)
            chosen, source = self.decide(triage_text)
            ctx.set_state("route", chosen)
            ctx.set_state("route_name", self._display_names.get(chosen, chosen))
            ctx.set_state("route_source", source)
            prompt = ctx.get_state("prompt") or ""
            await ctx.send_message(
                make_request(f"Triage routed this to you.\nRequest:\n{prompt}\n\nTriage notes:\n{triage_text}"),
                target_id=chosen,
            )
    ''',
        ),
        (
            "HandoffFinisherGateExecutor: hand off to a fixed finisher",
            PRIMITIVE,
            "When the scenario declares a finisher, every routed specialist's output flows "
            "through this gate to that fixed owner -- guaranteeing the run ends with the same "
            "accountable closing step (a customer letter, a final packet) no matter which route "
            "was taken. Route variance in the middle, an invariant ending: a very common "
            "compliance shape.",
            r'''
    class HandoffFinisherGateExecutor(Executor):
        @handler
        async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            route = ctx.get_state("route_name") or ctx.get_state("route") or "specialist"
            transcript = _append_transcript(ctx, route, response_text(response))
            prompt = ctx.get_state("prompt") or ""
            carried = "\n".join(transcript)
            await ctx.send_message(
                make_request(
                    f"You are the finishing stage of a handoff.\nOriginal request:\n{prompt}\n\n"
                    f"Routed specialist notes:\n{carried}\n\nComplete the final deliverable."
                )
            )
    ''',
        ),
        (
            "HandoffOutputExecutor: yield with a route header",
            PRIMITIVE,
            "The terminal `Executor` for handoff runs: it yields the answer prefixed with a "
            "`[routed to X via Y]` header, where Y is `model-directive` or `keyword-score`. That "
            "header is deliberately part of the output -- when you evaluate a handoff system, how "
            "often the model's routing was usable (versus rescued by the keyword fallback) is a "
            "metric you want visible on every run.",
            r'''
    class HandoffOutputExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str | None = None) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            route = ctx.get_state("route_name") or ctx.get_state("route") or "specialist"
            source = ctx.get_state("route_source") or "keyword-score"
            header = f"[routed to {route} via {source}]"
            if self._stage_name is None:
                await ctx.yield_output(f"{header}\n{response_text(response)}")
                return
            transcript = _append_transcript(ctx, self._stage_name, response_text(response))
            await ctx.yield_output("\n\n".join([header, *transcript]))
    ''',
        ),
        (
            "Derive routing keywords",
            SUPPORT,
            "Builds each specialist's keyword list -- the explicit `route_keywords` when the spec "
            "declares them, otherwise tokens derived from the agent's name and description with "
            "stopwords removed. This fallback vocabulary is the router's safety net when the "
            "model emits no usable directive, so skim it: if two specialists share their "
            "strongest keywords, ambiguous inputs will route unpredictably.",
            r'''
    def _route_keywords(spec: AgentSpec) -> tuple[str, ...]:
        if spec.route_keywords:
            return tuple(spec.route_keywords)
        tokens = re.findall(r"[a-z]+", f"{spec.name} {spec.description}".lower())
        keywords = [token for token in tokens if len(token) > 3 and token not in _STOPWORDS]
        return tuple(dict.fromkeys(keywords))[:6]
    ''',
        ),
        (
            "Preview routing",
            SUPPORT,
            "An offline check -- no model call -- that exercises the router both ways: a well- "
            "formed ROUTE directive winning, then the keyword fallback scoring the sample prompt. "
            "Rerun it after editing any instruction or keyword; it is the fastest way to catch a "
            "routing regression before spending a live run on it.",
            r'''
    # Demo (offline): a valid ROUTE directive wins; keyword scoring is the fallback.
    _specialists = [spec for spec in SCENARIO.agents[1:] if spec.name != SCENARIO.handoff_finisher]
    _demo_routes = {_route_slug(spec.name): _route_keywords(spec) for spec in _specialists}
    _demo_names = {_route_slug(spec.name): spec.name for spec in _specialists}
    _demo_router = HandoffRouterExecutor(
        id="demo_router", routes=_demo_routes, default_route=next(iter(_demo_routes)), display_names=_demo_names
    )
    print("directive ->", _demo_router.choose("Triage notes.\nROUTE: " + _specialists[-1].name))
    print("keywords  ->", _demo_router.choose(SAMPLE_PROMPT))
    ''',
        ),
    ],
    'group-chat': [
        (
            "Termination condition",
            SUPPORT,
            "A factory returning the `should_stop(messages)` closure that `GroupChatBuilder` "
            "evaluates as the chat proceeds. It only fires at full-cycle boundaries -- assistant "
            "count divisible by participant count -- which is the mechanism guaranteeing the "
            "closing agent always speaks last; it then stops early if the scenario's termination "
            "phrases all appear in that closing message, and unconditionally after two cycles. "
            "Termination is the hardest part of group chat to get right: too eager truncates the "
            "debate, too lax burns tokens.",
            r'''
    def make_group_chat_termination(phrases: tuple[str, ...], participant_count: int, max_cycles: int = 2) -> Any:
        def should_stop(messages: list[Any]) -> bool:
            assistant = [m for m in messages if getattr(m, "role", None) == "assistant"]
            if not assistant or len(assistant) % participant_count != 0:
                return False
            if len(assistant) >= max_cycles * participant_count:
                return True
            last_text = (getattr(assistant[-1], "text", "") or "").lower()
            return bool(phrases) and all(phrase in last_text for phrase in phrases)

        return should_stop
    ''',
        ),
        (
            "Preview termination",
            SUPPORT,
            "An offline check -- no model call -- probing the termination closure with tiny "
            "stand-in messages: mid-cycle with the phrase present (must not stop), a cycle end "
            "without it (must not stop), a cycle end with it (stops), and the hard two-cycle cap. "
            "Four probes that document the contract better than prose could.",
            r'''
    # Demo (offline): termination only fires when the closing agent ends a full cycle.
    class _DemoMsg:
        def __init__(self, text: str) -> None:
            self.role = "assistant"
            self.text = text


    _n = len(SCENARIO.agents)
    _phrase = " ".join(SCENARIO.termination_phrases) or "final recommendation"
    _stop = make_group_chat_termination(SCENARIO.termination_phrases, _n)
    print("mid-cycle, phrase present  ->", _stop([_DemoMsg(_phrase)] * max(1, _n - 1)))
    print("cycle end, no phrase       ->", _stop([_DemoMsg("still debating")] * _n))
    print("cycle end, phrase present  ->", _stop([_DemoMsg("x")] * (_n - 1) + [_DemoMsg(_phrase)]))
    print("after two full cycles      ->", _stop([_DemoMsg("x")] * (2 * _n)))
    ''',
        ),
    ],
    'magentic': [
        (
            "Ledger limits",
            SUPPORT,
            "The bounds that keep the manager's plan/delegate/replan loop finite: at most 10 "
            "rounds, a reset after 3 stalled rounds, and at most 2 resets before the workflow "
            "gives up. It is just a dict here -- the coordination machinery lives in "
            "`MagenticBuilder` -- but these numbers are your main cost and latency lever when "
            "magentic goes to production.",
            r'''
    MAGENTIC_LIMITS = {"max_round_count": 10, "max_stall_count": 3, "max_reset_count": 2}
    ''',
        ),
        (
            "Preview the manager split",
            SUPPORT,
            "An offline check -- no model call -- printing which agent will act as manager "
            "(always the first in the roster), which agents are delegatable specialists, and the "
            "ledger limits in force. When a magentic run behaves oddly, confirming the "
            "manager/specialist split is the first diagnostic.",
            r'''
    # Demo (offline): the manager/specialist split and the ledger limits that bound replanning.
    print("Manager:    ", SCENARIO.agents[0].name)
    print("Specialists:", ", ".join(spec.name for spec in SCENARIO.agents[1:]))
    for _key, _value in MAGENTIC_LIMITS.items():
        print(f"{_key} = {_value}")
    ''',
        ),
    ],
}


def _segments_to_cells(segments: list[tuple[str, str, str, str]]) -> list[dict[str, Any]]:
    """Flatten (title, tag, body, code) teaching segments into notebook cells."""

    cells: list[dict[str, Any]] = []
    for title, tag, body, code_source in segments:
        cells.extend(teach(title, tag, body, code_source))
    return cells


def pattern_machinery_cells(pattern: str) -> list[dict[str, Any]]:
    return _segments_to_cells(_PATTERN_MACHINERY[pattern])


_PATTERN_BUILDS = {
    'sequential': [
        (
            "Wire the graph with WorkflowBuilder",
            PRIMITIVE,
            "`WorkflowBuilder` assembles the executors into a fixed graph: `start_executor` and "
            "`output_from` declare the ends, and `add_edge` chains dispatch -> agent -> gate -> "
            "agent ... -> output, weaving a `StageGateExecutor` between consecutive agents. Read "
            "the loop and notice what is absent -- no model input, no branching. The topology is "
            "decided entirely in code, which is the sequential pattern's promise.",
            r'''
    def build_sequential_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        agents = [_agent_executor(i, scenario, config=config) for i in range(len(scenario.agents))]
        dispatch = PromptDispatchExecutor(id="dispatch")
        output = SequentialOutputExecutor(id="final_output", stage_name=scenario.agents[-1].name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_edge(dispatch, agents[0])
        for index in range(len(agents) - 1):
            gate = StageGateExecutor(id=f"gate_{index}", stage_name=scenario.agents[index].name)
            builder.add_edge(agents[index], gate)
            builder.add_edge(gate, agents[index + 1])
        builder.add_edge(agents[-1], output)
        return builder.build()
    ''',
        ),
        (
            "Compile and build",
            SUPPORT,
            "`build_workflow` resolves the Ollama config (model, host, and this scenario's token "
            "budget) and hands it to the builder above; `build()` then compiles the executor "
            "graph into a runnable workflow object. The wrapper is notebook glue so later cells "
            "can rebuild with overrides -- try `build_workflow(max_tokens=250)` for a faster "
            "smoke run -- while `build()` is the actual framework call. The printed type confirms "
            "what the framework produced.",
            r'''
    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        return build_sequential_workflow(scenario, config=config)


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    print(
        f"Built the {SCENARIO.pattern} workflow over {len(SCENARIO.agents)} agents: "
        + type(workflow).__name__
    )
    ''',
        ),
    ],
    'concurrent': [
        (
            "Wire fan-out and fan-in with WorkflowBuilder",
            PRIMITIVE,
            "`add_fan_out_edges` gives the dispatch node an edge to every lane at once, and "
            "`add_fan_in_edges` declares that the collector receives all of their responses as "
            "one list -- these two calls are the entire concurrency story; no threads or queues "
            "appear in user code. The builder then branches on the scenario: with a synthesizer, "
            "fan-in feeds the synthesis gate and one more agent runs before output; without one, "
            "fan-in terminates at the aggregator.",
            r'''
    def build_concurrent_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        synthesizer_name = scenario.concurrent_synthesizer
        parallel = [i for i in range(len(scenario.agents)) if scenario.agents[i].name != synthesizer_name]
        agents = [_agent_executor(i, scenario, config=config) for i in parallel]
        parallel_names = [scenario.agents[i].name for i in parallel]
        dispatch = PromptDispatchExecutor(id="dispatch")
        if synthesizer_name is None:
            aggregator = ConcurrentAggregatorExecutor(id="aggregator", agent_names=parallel_names)
            builder = WorkflowBuilder(start_executor=dispatch, output_from=[aggregator])
            builder.add_fan_out_edges(dispatch, agents)
            builder.add_fan_in_edges(agents, aggregator)
            return builder.build()
        synthesizer_index = next(
            i for i in range(len(scenario.agents)) if scenario.agents[i].name == synthesizer_name
        )
        synthesizer = _agent_executor(synthesizer_index, scenario, config=config)
        gate = ConcurrentSynthesisGateExecutor(id="synthesis_gate", agent_names=parallel_names)
        output = SequentialOutputExecutor(id="final_output", stage_name=synthesizer_name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_fan_out_edges(dispatch, agents)
        builder.add_fan_in_edges(agents, gate)
        builder.add_edge(gate, synthesizer)
        builder.add_edge(synthesizer, output)
        return builder.build()
    ''',
        ),
        (
            "Compile and build",
            SUPPORT,
            "`build_workflow` resolves the Ollama config (model, host, and this scenario's token "
            "budget) and hands it to the builder above; `build()` then compiles the executor "
            "graph into a runnable workflow object. The wrapper is notebook glue so later cells "
            "can rebuild with overrides -- try `build_workflow(max_tokens=250)` for a faster "
            "smoke run -- while `build()` is the actual framework call. The printed type confirms "
            "what the framework produced.",
            r'''
    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        return build_concurrent_workflow(scenario, config=config)


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    print(
        f"Built the {SCENARIO.pattern} workflow over {len(SCENARIO.agents)} agents: "
        + type(workflow).__name__
    )
    ''',
        ),
    ],
    'handoff': [
        (
            "Wire triage, router, and specialists with WorkflowBuilder",
            PRIMITIVE,
            "The graph runs dispatch -> triage -> router, then `add_edge`s the router to every "
            "specialist -- but at runtime the router's `target_id` picks exactly one of those "
            "edges to use. Compare the two closing shapes: without a finisher each specialist "
            "connects straight to output; with one, every specialist funnels through the finisher "
            "gate to the fixed owner. Edges define what is possible; the router decides what "
            "happens.",
            r'''
    def build_handoff_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        triage = _agent_executor(0, scenario, config=config)
        finisher_name = scenario.handoff_finisher
        routable = [i for i in range(1, len(scenario.agents)) if scenario.agents[i].name != finisher_name]
        specialists = [_agent_executor(i, scenario, config=config) for i in routable]
        specialist_ids = [_slug(scenario.agents[i].name) for i in routable]
        routes = {specialist_ids[pos]: _route_keywords(scenario.agents[i]) for pos, i in enumerate(routable)}
        display_names = {specialist_ids[pos]: scenario.agents[i].name for pos, i in enumerate(routable)}
        dispatch = PromptDispatchExecutor(id="dispatch")
        router = HandoffRouterExecutor(
            id="router", routes=routes, default_route=specialist_ids[0], display_names=display_names
        )
        output = HandoffOutputExecutor(id="final_output", stage_name=finisher_name)
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_edge(dispatch, triage)
        builder.add_edge(triage, router)
        if finisher_name is None:
            for specialist in specialists:
                builder.add_edge(router, specialist)
                builder.add_edge(specialist, output)
            return builder.build()
        finisher_index = next(
            i for i in range(1, len(scenario.agents)) if scenario.agents[i].name == finisher_name
        )
        finisher = _agent_executor(finisher_index, scenario, config=config)
        finisher_gate = HandoffFinisherGateExecutor(id="finisher_gate")
        for specialist in specialists:
            builder.add_edge(router, specialist)
            builder.add_edge(specialist, finisher_gate)
        builder.add_edge(finisher_gate, finisher)
        builder.add_edge(finisher, output)
        return builder.build()
    ''',
        ),
        (
            "Compile and build",
            SUPPORT,
            "`build_workflow` resolves the Ollama config (model, host, and this scenario's token "
            "budget) and hands it to the builder above; `build()` then compiles the executor "
            "graph into a runnable workflow object. The wrapper is notebook glue so later cells "
            "can rebuild with overrides -- try `build_workflow(max_tokens=250)` for a faster "
            "smoke run -- while `build()` is the actual framework call. The printed type confirms "
            "what the framework produced.",
            r'''
    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        return build_handoff_workflow(scenario, config=config)


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    print(
        f"Built the {SCENARIO.pattern} workflow over {len(SCENARIO.agents)} agents: "
        + type(workflow).__name__
    )
    ''',
        ),
    ],
    'group-chat': [
        (
            "Assemble the chat with GroupChatBuilder",
            PRIMITIVE,
            "`GroupChatBuilder` is a higher-level primitive than `WorkflowBuilder`: hand it the "
            "participants, a `selection_func` (plain round-robin here -- code, not a model, picks "
            "who speaks), the termination closure from the previous section, and "
            "`intermediate_output_from` so every turn surfaces in the results, and `build()` "
            "returns the runnable chat. Swapping the selector for something smarter -- a "
            "moderator model, expertise matching -- is the natural first experiment once you "
            "outgrow round-robin.",
            r'''
    def build_group_chat_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        from agent_framework.orchestrations import GroupChatBuilder

        participants = _agents_for(scenario, config=config)

        def round_robin_selector(state: Any) -> str:
            participant_names = list(state.participants.keys())
            return participant_names[state.current_round % len(participant_names)]

        return GroupChatBuilder(
            participants=participants,
            selection_func=round_robin_selector,
            termination_condition=make_group_chat_termination(
                scenario.termination_phrases, len(scenario.agents)
            ),
            intermediate_output_from=participants,
        ).build()
    ''',
        ),
        (
            "Compile and build",
            SUPPORT,
            "`build_workflow` resolves the Ollama config (including this scenario's 1500-token "
            "budget -- debate turns need room) and calls the builder above. The wrapper is "
            "notebook glue; `GroupChatBuilder(...).build()` is the framework call, and the "
            "printed type shows the chat compiles to the same workflow machinery as the graph "
            "patterns.",
            r'''
    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        return build_group_chat_workflow(scenario, config=config)


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    print(
        f"Built the {SCENARIO.pattern} workflow over {len(SCENARIO.agents)} agents: "
        + type(workflow).__name__
    )
    ''',
        ),
    ],
    'magentic': [
        (
            "Assemble the manager loop with MagenticBuilder",
            PRIMITIVE,
            "`MagenticBuilder` wires the roster's first agent in as `manager_agent` and the rest "
            "as delegatable `participants`, applies the ledger limits, and `build()` returns the "
            "runnable workflow. Unlike every other builder in this repo, the resulting run's "
            "shape is decided at runtime by the manager's planning -- the builder defines who "
            "exists and the bounds, not the order of work.",
            r'''
    def build_magentic_workflow(scenario: ScenarioSpec, *, config: OllamaAgentConfig) -> Any:
        from agent_framework.orchestrations import MagenticBuilder

        agents = _agents_for(scenario, config=config)
        manager_agent = agents[0]
        participants = agents[1:]
        return MagenticBuilder(
            participants=participants,
            intermediate_output_from=participants,
            manager_agent=manager_agent,
            **MAGENTIC_LIMITS,
        ).build()
    ''',
        ),
        (
            "Compile and build",
            SUPPORT,
            "`build_workflow` resolves the Ollama config (including this scenario's 1500-token "
            "budget -- planning and replanning are token-hungry) and calls the builder above. The "
            "wrapper is notebook glue; `MagenticBuilder(...).build()` is the framework call. "
            "Expect this workflow to issue more LLM calls than any other pattern in the repo.",
            r'''
    def build_workflow(
        scenario: ScenarioSpec = SCENARIO,
        *,
        max_tokens: int | None = None,
        **config_overrides: Any,
    ) -> Any:
        config = build_ollama_config(max_tokens=max_tokens or MAX_TOKENS, **config_overrides)
        return build_magentic_workflow(scenario, config=config)


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    print(
        f"Built the {SCENARIO.pattern} workflow over {len(SCENARIO.agents)} agents: "
        + type(workflow).__name__
    )
    ''',
        ),
    ],
}


def build_cells(pattern: str) -> list[dict[str, Any]]:
    return _segments_to_cells(_PATTERN_BUILDS[pattern])


def results_cell(include_group_summary: bool) -> str:
    body = _RESULTS_BASE + (_RESULTS_GROUP_SUMMARY if include_group_summary else "")
    return body + _RESULTS_PRINT


_RESULTS_BASE = r'''
    from collections.abc import Mapping, Sequence


    def workflow_result_to_text(result: Any) -> str:
        outputs = result.get_outputs() if hasattr(result, "get_outputs") else result
        intermediate = result.get_intermediate_outputs() if hasattr(result, "get_intermediate_outputs") else []
        if not outputs:
            intermediate_text = join_readable_outputs(intermediate)
            return clean_workflow_text(intermediate_text) or "No workflow output was produced."
        output_text = join_readable_outputs(outputs)
        if intermediate and should_use_intermediate_outputs(output_text):
            intermediate_text = join_readable_outputs(intermediate)
            if intermediate_text:
                return clean_workflow_text(intermediate_text)
        return clean_workflow_text(output_text) or "No readable workflow text was produced."


    def join_readable_outputs(outputs: Any) -> str:
        return "\n\n".join(text for output in outputs if (text := agent_response_to_text(output)))


    def should_use_intermediate_outputs(output_text: str) -> bool:
        normalized = output_text.strip().lower()
        if not normalized:
            return True
        if len(normalized) >= 160:
            return False
        markers = (
            "termination condition",
            "maximum reset count",
            "maximum stall count",
            "workflow terminated",
            "group chat has reached its termination condition",
        )
        return any(marker in normalized for marker in markers)


    def agent_response_to_text(value: Any) -> str:
        text = clean_workflow_text(extract_text(value))
        return text


    def clean_workflow_text(text: str) -> str:
        """Remove leading framework status lines when useful scenario text follows."""

        lines = text.splitlines()
        while lines and is_framework_status_line(lines[0]) and any(line.strip() for line in lines[1:]):
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
        return "\n".join(lines).strip()


    def is_framework_status_line(line: str) -> bool:
        normalized = line.strip().lower()
        return (
            normalized.startswith("invalid next speaker:")
            or normalized.startswith("magentic orchestrator:")
            or normalized.startswith("maximum consecutive function call errors reached")
        )


    def extract_text(value: Any, seen: set[int] | None = None) -> str:
        if value is None:
            return ""
        if seen is None:
            seen = set()
        value_id = id(value)
        if value_id in seen:
            return ""
        seen.add(value_id)
        if isinstance(value, str):
            return "" if is_object_repr(value) else value
        text = getattr(value, "text", None)
        if isinstance(text, str) and text and not is_object_repr(text):
            return text
        messages = getattr(value, "messages", None)
        if messages:
            parts: list[str] = []
            for message in messages:
                author = getattr(message, "author_name", None) or getattr(message, "role", None) or "assistant"
                message_text = extract_text(message, seen)
                if message_text:
                    parts.append(f"[{author}] {message_text}")
            if parts:
                return "\n".join(parts)
        contents = getattr(value, "contents", None)
        if contents:
            return "\n".join(part for content in contents if (part := extract_text(content, seen)))
        items = getattr(value, "items", None)
        if items and not callable(items):
            return "\n".join(part for item in items if (part := extract_text(item, seen)))
        result = getattr(value, "result", None)
        if result is not None:
            return extract_text(result, seen)
        if isinstance(value, Mapping):
            parts = [extract_text(value.get(key), seen) for key in ("text", "content", "message", "summary", "result")]
            return "\n".join(part for part in parts if part)
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            return "\n".join(part for item in value if (part := extract_text(item, seen)))
        fallback = str(value)
        return "" if is_object_repr(fallback) else fallback


    def is_object_repr(value: str) -> bool:
        return value.startswith("<") and " object at 0x" in value and value.endswith(">")


    '''

_RESULTS_GROUP_SUMMARY = r'''
    def group_chat_learning_summary(
        scenario: ScenarioSpec,
        prompt: str,
        framework_text: str,
    ) -> str:
        """Explain a completed group-chat run when this framework build hides the transcript."""

        lines = [
            "Group chat completed.",
            "",
            f"Framework result: {framework_text.strip()}",
            "",
            "Learning view:",
            "- The workflow used Microsoft Agent Framework's GroupChatBuilder with LLM-backed participants.",
            "- Selection is code-defined round robin; termination is code-defined from assistant messages.",
            f"- The submitted scenario prompt was: {prompt}",
            "- Participant order:",
        ]
        for index, spec in enumerate(scenario.agents, start=1):
            tools = ", ".join(spec.mcp_tools) if spec.mcp_tools else "no domain tools"
            lines.append(f"  {index}. {spec.name}: {spec.description} ({tools})")
        tool_names = sorted({tool for spec in scenario.agents for tool in spec.mcp_tools})
        if tool_names:
            lines.append("- Grounding sources available to tool-enabled agents:")
            for tool_name in tool_names:
                lines.append(f"  - {tool_name}")
        lines.extend(
            [
                "",
                "Note: this local Agent Framework build returned the group-chat termination marker",
                "without exposing participant turns through get_intermediate_outputs(). The notebook",
                "keeps the framework run intact and prints this learning summary so the scenario",
                "still explains the orchestration shape and agent responsibilities.",
            ]
        )
        return "\n".join(lines)
    '''

_RESULTS_PRINT = r'''

    print("Result formatting ready: workflow_result_to_text(...) turns framework events "
          "into readable text.")
    '''


_DIAGRAM_HEAD = r'''
    import base64
    import html
    from dataclasses import dataclass

    from IPython.display import HTML, display


    @dataclass(frozen=True)
    class ScenarioFlowDiagram:
        title: str
        mermaid: str
        image_url: str


    def scenario_flow_diagram(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        mermaid = __DIAGRAM_FN__(scenario, api_boundary="{api_boundary}", input_label="{input_label}")
        return ScenarioFlowDiagram(
            title=f"{{scenario.title}} Flow",
            mermaid=mermaid,
            image_url=_mermaid_image_url(mermaid),
        )


    def display_scenario_flow(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        diagram = scenario_flow_diagram(scenario)
        display(
            HTML(
                '<figure style="margin: 0">'
                f'<img src="{{html.escape(diagram.image_url)}}" alt="{{html.escape(diagram.title)}}" '
                'style="max-width: 100%; height: auto;" />'
                f'<figcaption style="font-size: 0.9em; color: #555;">{{html.escape(diagram.title)}}</figcaption>'
                "</figure>"
            )
        )
        return diagram


'''

_DIAGRAM_BODIES = {
    'sequential': r'''
    def _sequential_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        previous = "orchestrator"
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(scenario.agents, start=1):
            node = f"agent{{index}}"
            lines.append(f"    {{previous}} -->|stage {{index}}| {{node}}[{{_label(agent.name)}}]")
            previous = node
            pairs.append((agent, node))
        lines.append(f"    {{previous}} --> output[{output_label}]")
        lines.extend(_mcp_tool_links(pairs))
        return "\n".join(lines)


''',
    'concurrent': r'''
    def _concurrent_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        synthesizer = next(
            (agent for agent in scenario.agents if agent.name == scenario.concurrent_synthesizer), None
        )
        parallel = [agent for agent in scenario.agents if agent is not synthesizer]
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append("    orchestrator --> fanout{{Fan out same request}}")
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(parallel, start=1):
            node = f"agent{{index}}"
            lines.append(f"    fanout --> {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> aggregate{{{{Aggregate findings}}}}")
            pairs.append((agent, node))
        if synthesizer is None:
            lines.append("    aggregate --> output[{output_label}]")
        else:
            lines.append(f"    aggregate --> synthesizer[{{_label(synthesizer.name)}}]")
            lines.append("    synthesizer --> output[{output_label}]")
            pairs.append((synthesizer, "synthesizer"))
        lines.extend(_mcp_tool_links(pairs))
        return "\n".join(lines)


''',
    'handoff': r'''
    def _handoff_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        triage, *others = scenario.agents
        finisher = next((agent for agent in others if agent.name == scenario.handoff_finisher), None)
        specialists = [agent for agent in others if agent is not finisher]
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append(f"    orchestrator --> triage[{{_label(triage.name)}}]")
        lines.append("    triage --> decision{{Ownership decision}}")
        pairs: list[tuple[AgentSpec, str]] = [(triage, "triage")]
        sink = "output[{output_label}]"
        if finisher is not None:
            lines.append(f"    finisher[{{_label(finisher.name)}}] --> output[{output_label}]")
            pairs.append((finisher, "finisher"))
            sink = "finisher"
        for index, agent in enumerate(specialists, start=1):
            node = f"specialist{{index}}"
            lines.append(f"    decision -->|handoff| {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> {{sink}}")
            pairs.append((agent, node))
        lines.extend(_mcp_tool_links(pairs))
        return "\n".join(lines)


''',
    'group-chat': r'''
    def _group_chat_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append("    orchestrator --> selector{{Round-robin selector}}")
        previous = "selector"
        pairs: list[tuple[AgentSpec, str]] = []
        for index, agent in enumerate(scenario.agents, start=1):
            node = f"agent{{index}}"
            lines.append(f"    {{previous}} --> {{node}}[{{_label(agent.name)}}]")
            previous = node
            pairs.append((agent, node))
        lines.append(f"    {{previous}} --> stop{{{{Termination condition}}}}")
        lines.append("    stop -->|continue| selector")
        lines.append("    stop -->|done| output[{output_label}]")
        remote_nodes = [node for agent, node in pairs if getattr(agent, "a2a_url", None)]
        if remote_nodes:
            lines.append("    subgraph partner_org[Partner organizations via A2A]")
            for node in remote_nodes:
                lines.append(f"        {{node}}")
            lines.append("    end")
            for node in remote_nodes:
                lines.append(f"    {{node}} -.->|A2A JSON-RPC| a2a_card([agent card])")
        lines.extend(_mcp_tool_links(pairs))
        return "\n".join(lines)


''',
    'magentic': r'''
    def _magentic_diagram(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> str:
        manager, *specialists = scenario.agents
        lines = _header(scenario, api_boundary=api_boundary, input_label=input_label)
        lines.append(f"    orchestrator --> manager[{{_label(manager.name)}}]")
        lines.append("    manager --> plan{{Plan and delegate}}")
        pairs: list[tuple[AgentSpec, str]] = [(manager, "manager")]
        for index, agent in enumerate(specialists, start=1):
            node = f"specialist{{index}}"
            lines.append(f"    plan --> {{node}}[{{_label(agent.name)}}]")
            lines.append(f"    {{node}} --> progress{{{{Progress ledger}}}}")
            pairs.append((agent, node))
        lines.append("    progress -->|replan| manager")
        lines.append("    progress -->|complete or stop| output[{output_label}]")
        lines.extend(_mcp_tool_links(pairs))
        return "\n".join(lines)


''',
}

_DIAGRAM_TAIL = r'''
    def _header(scenario: ScenarioSpec, *, api_boundary: str, input_label: str) -> list[str]:
        return [
            "%%{{init: {{'theme': 'neutral'}}}}%%",
        "flowchart TD",
            f"    client[{{_label(input_label)}}] --> api[{{_label(api_boundary)}}]",
            f"    api --> scenario[{{_label('Scenario: ' + scenario.id)}}]",
            f"    scenario --> orchestrator{{{{{{_label(scenario.pattern + ' orchestration')}}}}}}",
        ]


    def _mcp_tool_links(pairs: list[tuple[AgentSpec, str]]) -> list[str]:
        lines: list[str] = []
        for agent, node_id in pairs:
            for tool in agent.mcp_tools:
                lines.append(f"    {{node_id}} -.->|mcp tool| tool_{{tool}}([{{_label(tool)}}])")
        return lines


    def quote_to_cash_flow_diagram(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        mermaid = _quote_to_cash_source(scenario, api_boundary="{api_boundary}")
        return ScenarioFlowDiagram(
            title=f"{{scenario.title}} Quote-To-Cash Flow",
            mermaid=mermaid,
            image_url=_mermaid_image_url(mermaid),
        )


    def display_quote_to_cash_flow(scenario: ScenarioSpec) -> ScenarioFlowDiagram:
        diagram = quote_to_cash_flow_diagram(scenario)
        display(
            HTML(
                '<figure style="margin: 0">'
                f'<img src="{{html.escape(diagram.image_url)}}" alt="{{html.escape(diagram.title)}}" '
                'style="max-width: 100%; height: auto;" />'
                f'<figcaption style="font-size: 0.9em; color: #555;">{{html.escape(diagram.title)}}</figcaption>'
                "</figure>"
            )
        )
        return diagram


    def _quote_to_cash_source(scenario: ScenarioSpec, *, api_boundary: str) -> str:
        names = {{agent.name for agent in scenario.agents}}

        def node(role: str) -> str:
            return role if role in names else next(iter(names))

        lines = [
            "%%{{init: {{'theme': 'neutral'}}}}%%",
        "flowchart TD",
            f"    client[{{_label('Quote request begins in CRM')}}] --> api[{{_label(api_boundary)}}]",
            f"    api --> scenario[{{_label('Scenario: ' + scenario.id)}}]",
            f"    scenario --> orchestrator{{{{{{_label(scenario.pattern + ' orchestration')}}}}}}",
            f"    orchestrator --> crm[{{_label('CRM system')}}]",
            f"    crm -->|wave 1| trigger[{{_label(node('QuoteTriggerAgent'))}}]",
            f"    crm -->|wave 1| customer[{{_label(node('CustomerContextAgent'))}}]",
            f"    trigger --> store1[({{_label('Orchestration store: customer context')}})]",
            "    customer --> store1",
            f"    store1 -. {{_label('deallocate wave 1')}} .-> freed1(({{_label('agents released')}}))",
            f"    store1 --> product[{{_label('Product / SKU system')}}]",
            f"    product -->|wave 2| sku[{{_label(node('SkuDiscoveryAgent'))}}]",
            f"    product -->|wave 2| fit[{{_label(node('ProductFitAgent'))}}]",
            f"    sku --> store2[({{_label('Orchestration store: product context')}})]",
            "    fit --> store2",
            f"    store2 -. {{_label('deallocate wave 2')}} .-> freed2(({{_label('agents released')}}))",
            f"    store2 --> pricingsys[{{_label('Pricing / finance / legal system')}}]",
            f"    pricingsys -->|wave 3| pricing[{{_label(node('PricingTermsAgent'))}}]",
            f"    pricing --> generation[{{_label(node('QuoteGenerationAgent'))}}]",
            f"    generation --> quote[/{{_label('Final quote package')}}/]",
        ]
        return "\n".join(lines)


    def _label(value: str) -> str:
        return value.replace('"', "'")


    def _mermaid_image_url(mermaid: str) -> str:
        encoded = base64.urlsafe_b64encode(mermaid.encode("utf-8")).decode("ascii").rstrip("=")
        return f"https://mermaid.ink/img/{{encoded}}"


    flow_diagram = display_scenario_flow(SCENARIO){quote_call}
    print(flow_diagram.mermaid)
'''


def diagram_cell(project: dict[str, str], pattern: str, is_quote_to_cash: bool) -> str:
    quote_call = (
        "\n    quote_to_cash_diagram = display_quote_to_cash_flow(SCENARIO)" if is_quote_to_cash else ""
    )
    body = _DIAGRAM_HEAD.replace("__DIAGRAM_FN__", _DIAGRAM_FN_NAMES[pattern])
    body = body + _DIAGRAM_BODIES[pattern] + _DIAGRAM_TAIL
    return body.format(
        api_boundary=project["api_boundary"],
        input_label=project["input_label"],
        output_label=project["output_label"],
        quote_call=quote_call,
    )


_DIAGRAM_FN_NAMES = {'sequential': '_sequential_diagram', 'concurrent': '_concurrent_diagram', 'handoff': '_handoff_diagram', 'group-chat': '_group_chat_diagram', 'magentic': '_magentic_diagram'}


def live_run_cell() -> str:
    return r'''
    import io
    from contextlib import redirect_stderr, redirect_stdout


    workflow = build_workflow(SCENARIO, max_tokens=MAX_TOKENS)
    _framework_logs = io.StringIO()
    with redirect_stdout(_framework_logs), redirect_stderr(_framework_logs):
        result = await workflow.run(SAMPLE_PROMPT)
    framework_logs = _framework_logs.getvalue()
    output_text = workflow_result_to_text(result)
    if SCENARIO.pattern == "group-chat" and should_use_intermediate_outputs(output_text):
        output_text = group_chat_learning_summary(SCENARIO, SAMPLE_PROMPT, output_text)

    if not output_text.strip():
        raise RuntimeError("Workflow completed but produced no readable text.")

    render_transcript(output_text)
    '''


def flow_diagram_markdown(project: dict[str, str], scenario: Any) -> str:
    pattern = scenario.pattern
    n = len(scenario.agents)
    if pattern == "sequential":
        shape = "a linear chain of " + str(n) + " stages with a stage-gate executor between each pair"
    elif pattern == "concurrent":
        shape = "a fan-out to " + str(n) + " specialists and a labelled fan-in aggregation"
    elif pattern == "handoff":
        shape = "a triage node routing to one of " + str(n - 1) + " specialists via keyword scoring"
    elif pattern == "group-chat":
        shape = str(n) + " participants in a round-robin loop with a code-defined termination function"
    else:
        shape = "a manager agent delegating to " + str(n - 1) + " specialists with progress-ledger replanning"
    boundary = project["api_boundary"]
    return f"""
    ## Flow Diagram

    The diagram below shows {shape} attached to the {boundary}.
    Solid arrows are orchestration edges. Dashed arrows (`-.->`) are tool calls.
    Domain tool nodes use a stadium shape.
    """


def live_run_markdown(scenario: Any) -> str:
    intro = PATTERN_LIVE_RUN_INTRO[scenario.pattern]
    return f"""
    ## Live Run

    {intro}

    > **Instructor note:** `gemma4:12b` runs with `think: False` by default in this repo.
    > Set `OLLAMA_THINK=true` before the environment cell to enable chain-of-thought reasoning --
    > useful when debugging unexpected routing decisions or tool call sequences.
    """


def post_run_markdown(scenario: Any) -> str:
    inspect = PATTERN_INSPECT[scenario.pattern]
    spotlight = SCENARIO_SPOTLIGHTS[scenario.id][0]
    return f"""
    ## What to Inspect

    {inspect}

    > **Scenario spotlight:** {spotlight}
    """


def experiments_markdown(project: dict[str, str], scenario: Any) -> str:
    if project["sample_attr"] == "sample_input":
        payload_line = "`RESPONSES_PAYLOAD['input']`"
    else:
        payload_line = "`INVOCATION_PAYLOAD['task']`, `subject`, `artifacts`, or `constraints`"
    spotlight_experiment = SCENARIO_SPOTLIGHTS[scenario.id][1]
    return f"""
    ## Experiments

    - {spotlight_experiment}
    - Change {payload_line} and rerun the live cell.
    - Override `OLLAMA_MODEL` or `OLLAMA_HOST` before the environment cell to target a different local Ollama setup.
    - Inspect `agent_capability_map(SCENARIO)` and tighten one agent's instructions to see how orchestration behavior changes.
    - Lower `MAX_TOKENS` for faster smoke tests or raise it when {scenario.pattern} needs more room.
    """


ENTERPRISE_DEMO_CALLS = {
    "sequential-procurement-approval": 'lookup_enterprise_record("VENDOR-4471")',
    "concurrent-security-alert-enrichment": 'lookup_enterprise_record("ALERT-2298")',
    "handoff-claims-exception-routing": 'lookup_enterprise_record("CLAIM-88120")',
    "group-chat-policy-exception-board": 'lookup_enterprise_record("POLICY-EX-77")',
    "magentic-business-continuity-drill": 'lookup_enterprise_record("FACILITY-DC-EAST")',
    "sequential-loan-origination": 'lookup_enterprise_record("LOAN-73021")',
    "concurrent-ma-due-diligence": 'lookup_enterprise_record("TARGET-ACQ-STELLAR")',
    "handoff-transaction-dispute": 'lookup_enterprise_record("DISPUTE-90455")',
    "group-chat-architecture-review": 'lookup_enterprise_record("ADR-2209")',
    "magentic-churn-spike-investigation": 'lookup_enterprise_record("METRIC-CHURN-Q3")',
}


def primitives_title_markdown(project: dict[str, str], scenario: Any) -> str:
    return f"""
    # {scenario.title}

    | Field | Value |
    | --- | --- |
    | Scenario id | `{scenario.id}` |
    | Pattern used for server execution | `{scenario.pattern}` |
    | API | `{project['api_name']}` |
    | Recommended max tokens | `{scenario.max_tokens}` per agent turn |

    **Learning goal:** {scenario.learning_goal}

    > {scenario.when_to_use}

    This notebook is a primitive lab, not a single-pattern deep dive. Each cell
    introduces one practical Microsoft Agent Framework building block and ends
    with an observable artifact: a rendered card, trace entry, object summary,
    Mermaid diagram, or guarded live-run hook.
    """


def primitives_overview_markdown() -> str:
    return """
    ## Primitive Map

    Agent Framework has two large families of capability: **agents** and
    **workflows**. Agents wrap model-backed reasoning, tools, context, sessions,
    streaming, and remote-agent protocols. Workflows wire agents and code into
    explicit graphs with deterministic routing, state, fan-out/fan-in, and
    orchestration builders.

    This lab still uses the repo's **Instruction-Led LLM Agents** teaching
    style: every model-facing role has crisp instructions, explicit tool
    grants, and a visible runtime boundary.

    ## Pattern Anatomy

    | Primitive | Why it is in this lab |
    | --- | --- |
    | `Message` | The smallest unit of user/assistant/system exchange. |
    | Chat-client-backed agent | The common local prototype shape with Ollama. |
    | Function tool | The simplest grounded action an agent can call. |
    | Session/thread state | Keeps multi-turn context from becoming global state. |
    | Streaming | Lets UI and logs observe long-running model output. |
    | `MCPStdioTool` | Connects an agent to local or external tools through MCP. |
    | `A2AAgent` | Connects orchestration to a peer agent owned elsewhere. |
    | `Executor` + `@handler` | Custom code node in a workflow graph. |
    | `WorkflowContext` | Shared graph state, message sends, and outputs. |
    | `AgentExecutor` | Wraps an agent so it can sit inside a workflow graph. |
    | `WorkflowBuilder` | Explicit graph wiring for deterministic control. |
    | Fan-out/fan-in | Parallel lanes with deterministic aggregation. |
    | Handoff routing | Model-guided ownership, code-validated. |
    | `GroupChatBuilder` | Multi-agent discussion with selection and termination. |
    | `MagenticBuilder` | Manager-led planning and dynamic delegation. |
    | Hosting boundary | Responses and Invocations expose the same workflow differently. |
    | Observability | Trace events, transcript extraction, and visible state. |

    ## Excluded Here

    Hosted file search, hosted code interpreter, web search, Foundry toolboxes,
    durable workflow persistence, and cloud-specific memory providers are
    important but intentionally excluded. They require cloud credentials,
    provider-specific setup, or external state, while this repository is a
    local Ollama teaching workspace.
    """


def primitives_environment_cells() -> list[dict[str, Any]]:
    config = r'''
    import base64
    import html
    import json
    import os
    from dataclasses import dataclass
    from pprint import pprint
    from typing import Any

    from IPython.display import HTML, Markdown, display


    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
    DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    RUN_LIVE_AGENT = os.getenv("RUN_LIVE_AGENT", "0").lower() in {"1", "true", "yes"}
    '''

    styling = r'''
    _APTOS_STYLE = """
    <style>
    :root { --jp-content-font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif; }
    .jp-RenderedHTMLCommon, .jp-RenderedMarkdown, .rendered_html, .jp-OutputArea-output {
        font-family: 'Aptos', 'Segoe UI', 'Helvetica Neue', sans-serif;
        line-height: 1.55;
    }
    .jp-RenderedHTMLCommon h1, .jp-RenderedHTMLCommon h2, .jp-RenderedHTMLCommon h3 {
        font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif;
        font-weight: 650;
    }
    .primitive-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; }
    .primitive-card {
        border: 1px solid rgba(100, 116, 139, 0.35); border-radius: 8px; padding: 10px 12px;
        background: linear-gradient(180deg, rgba(248,250,252,.9), rgba(241,245,249,.9));
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }
    .primitive-card b { color: #1d4ed8; display: block; margin-bottom: 4px; }
    .primitive-chip {
        display: inline-block; border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0;
        background: #e0f2fe; color: #075985; font-size: 12px; font-weight: 600;
    }
    .trace-row {
        border-left: 4px solid #2563eb; margin: 6px 0; padding: 6px 10px;
        background: rgba(37, 99, 235, 0.08); border-radius: 6px;
    }
    .transcript-block {
        border: 1px solid rgba(100, 116, 139, 0.35); border-radius: 8px; padding: 10px 12px;
        background: rgba(255,255,255,.72); white-space: pre-wrap;
    }
    </style>
    """


    def apply_notebook_style() -> str:
        display(HTML(_APTOS_STYLE))
        return _APTOS_STYLE


    apply_notebook_style()
    '''

    renderers = r'''
    def render_cards(items: list[dict[str, str]]) -> None:
        cards = []
        for item in items:
            chips = "".join(f"<span class='primitive-chip'>{html.escape(chip)}</span>" for chip in item.get("chips", "").split("|") if chip)
            cards.append(
                "<div class='primitive-card'>"
                f"<b>{html.escape(item['title'])}</b>"
                f"<div>{html.escape(item['body'])}</div>"
                f"<div>{chips}</div>"
                "</div>"
            )
        display(HTML("<div class='primitive-grid'>" + "".join(cards) + "</div>"))


    def render_trace(events: list[dict[str, str]]) -> None:
        rows = [
            f"<div class='trace-row'><b>{html.escape(event['stage'])}</b>: {html.escape(event['detail'])}</div>"
            for event in events
        ]
        display(HTML("".join(rows)))


    def render_transcript(text: str) -> None:
        display(Markdown(text))


    def render_roster(scenario: Any) -> None:
        render_cards([
            {
                "title": spec.name,
                "body": spec.description,
                "chips": "agent|instructions" + ("|tools" if getattr(spec, "mcp_tools", ()) else ""),
            }
            for spec in scenario.agents
        ])


    render_trace([
        {"stage": "model", "detail": DEFAULT_MODEL},
        {"stage": "host", "detail": DEFAULT_HOST},
        {"stage": "live agent calls", "detail": "enabled" if RUN_LIVE_AGENT else "guarded off; set RUN_LIVE_AGENT=1"},
    ])
    '''

    return (
        teach(
            "Runtime configuration",
            SUPPORT,
            "Imports plus the Ollama model/host defaults and the `RUN_LIVE_AGENT` guard that "
            "keeps this lab offline by default -- every primitive demonstrates itself "
            "deterministically, and only the guarded cells touch a live model. Set "
            "`RUN_LIVE_AGENT=1` before this cell when you want the real calls. Setup only; no "
            "Agent Framework surface here.",
            config,
        )
        + teach(
            "Notebook styling",
            SUPPORT,
            "The Aptos look plus the card, chip, and trace CSS the lab's render helpers use to "
            "present each primitive visually. Styling is isolated in this one cell so every later "
            "cell can stay focused on exactly one framework concept. Pure presentation.",
            styling,
        )
        + teach(
            "Rendering helpers",
            SUPPORT,
            "`render_cards` lays concepts out as a grid, `render_trace` shows step-by-step event "
            "rows, and `render_transcript`/`render_roster` present agent output and the team. "
            "Each primitive section below ends by handing its result to one of these, so you "
            "always see the concept, not raw dicts. Glue for the lab, not framework API.",
            renderers,
        )
    )


def primitives_scenario_cells(project: dict[str, str], scenario: Any) -> list[dict[str, Any]]:
    sample_attr = project["sample_attr"]
    data = scenario_data(scenario, sample_attr)
    scenario_json = textwrap.indent(json.dumps(data, indent=2), "    ")
    payload_code = (
        'RESPONSES_PAYLOAD = {"input": SCENARIO.sample_input, "stream": False}'
        if sample_attr == "sample_input"
        else textwrap.dedent(
            '''
            INVOCATION_PAYLOAD = {
                "scenario": SCENARIO.id,
                "pattern": SCENARIO.pattern,
                "task": SCENARIO.sample_task,
                "subject": "agent-framework-primitives-lab",
                "artifacts": ["docs/README.md"],
                "constraints": ["One primitive per teaching cell", "Observable output in every cell"],
                "stream": False,
            }
            '''
        ).strip()
    )
    schema = f'''
    @dataclass(frozen=True)
    class AgentSpec:
        name: str
        description: str
        instructions: str
        mcp_tools: tuple[str, ...] = ()
        mcp_server: str = "enterprise_context"
        route_keywords: tuple[str, ...] = ()
        a2a_url: str | None = None


    @dataclass(frozen=True)
    class ScenarioSpec:
        id: str
        pattern: str
        title: str
        learning_goal: str
        when_to_use: str
        {sample_attr}: str
        agents: tuple[AgentSpec, ...]
        max_tokens: int
        handoff_finisher: str | None = None
        concurrent_synthesizer: str | None = None
        termination_phrases: tuple[str, ...] = ()
    '''

    hydrate = f'''
    SCENARIO_DATA = json.loads(
        r"""
{scenario_json}
        """
    )
    AGENTS = tuple(
        AgentSpec(
            name=agent["name"],
            description=agent["description"],
            instructions=agent["instructions"],
            mcp_tools=tuple(agent.get("mcp_tools", ())),
            mcp_server=agent.get("mcp_server", "enterprise_context"),
            route_keywords=tuple(agent.get("route_keywords", ())),
            a2a_url=agent.get("a2a_url"),
        )
        for agent in SCENARIO_DATA["agents"]
    )
    SCENARIO = ScenarioSpec(
        id=SCENARIO_DATA["id"],
        pattern=SCENARIO_DATA["pattern"],
        title=SCENARIO_DATA["title"],
        learning_goal=SCENARIO_DATA["learning_goal"],
        when_to_use=SCENARIO_DATA["when_to_use"],
        {sample_attr}=SCENARIO_DATA["{sample_attr}"],
        agents=AGENTS,
        max_tokens=SCENARIO_DATA["max_tokens"],
    )
    {payload_code}
    '''

    roster = f'''
    def agent_capability_map(scenario: ScenarioSpec) -> list[dict[str, Any]]:
        return [
            {{
                "agent": spec.name,
                "description": spec.description,
                "instructions": spec.instructions,
                "tools": list(spec.mcp_tools),
            }}
            for spec in scenario.agents
        ]


    render_roster(SCENARIO)
    print(json.dumps({{"scenario": SCENARIO.id, "pattern": SCENARIO.pattern, "api": "{project['api_name']}", "max_tokens": SCENARIO.max_tokens}}, indent=2))
    print(json.dumps(agent_capability_map(SCENARIO), indent=2))
    '''

    return (
        teach(
            "Scenario schema",
            SUPPORT,
            "Plain frozen dataclasses mirroring the scenario JSON -- the same "
            "`AgentSpec`/`ScenarioSpec` shapes the packaged scenarios use, including the per- "
            "scenario `max_tokens` budget. Keeping the contract in plain data is what lets one "
            "spec drive every orchestration builder this lab demonstrates. Not framework types.",
            schema,
        )
        + teach(
            "Load the scenario",
            SUPPORT,
            "Hydrates the embedded JSON into the `SCENARIO` object and the sample payload the "
            "rest of the lab reads. The same roster flows through every primitive below -- "
            "messages, tools, agents, and all five orchestration builders -- so you can watch one "
            "team of agents recur across concepts. Data plumbing only.",
            hydrate,
        )
        + teach(
            "Roster and capability map",
            SUPPORT,
            "`agent_capability_map` and `render_roster` show who is on the team, what each agent "
            "may call, and the scenario's token budget. Make roster inspection a reflex: when a "
            "later primitive behaves unexpectedly, the roster is where tool grants and role "
            "mismatches show up first. Supporting inspection, not Agent Framework surface.",
            roster,
        )
    )


def primitives_message_cell() -> str:
    return r'''
    # Primitive: Message
    from agent_framework import Message

    inbound = Message(role="user", contents=["Explain the primitive map for a local Agent Framework prototype."])
    system_hint = Message(role="system", contents=["Use concrete primitives, not marketing language."])

    MESSAGE_TRACE = [
        {"stage": "system message", "detail": str(system_hint.contents[0])},
        {"stage": "user message", "detail": str(inbound.contents[0])},
    ]
    render_trace(MESSAGE_TRACE)
    print("Message objects are the smallest portable unit passed to agents and workflow executors.")
    '''


def primitives_function_tool_cell() -> str:
    return r'''
    # Primitive: Function tool
    ENABLEMENT_FIXTURES = {
        "prototype": {"model": "gemma4:12b", "provider": "Ollama", "boundary": "local"},
        "budget": {"max_tokens": str(SCENARIO.max_tokens), "scope": "per agent turn"},
        "workflow": {"state": "WorkflowContext", "routing": "code-defined", "visibility": "trace events"},
        "protocols": {"tools": "MCP", "remote_agents": "A2A"},
    }


    def lookup_primitive_fact(topic: str) -> dict[str, str]:
        """A small function tool: deterministic, inspectable, and easy to test."""

        return ENABLEMENT_FIXTURES.get(topic, {"error": f"unknown topic: {topic}"})


    def draft_enablement_check(topic: str) -> str:
        fact = lookup_primitive_fact(topic)
        return "; ".join(f"{key}={value}" for key, value in fact.items())


    # Demo (offline): call the tool directly before any agent is allowed to use it.
    print(draft_enablement_check("workflow"))
    render_cards([
        {"title": "Function tool", "body": "Plain Python callable exposed to an agent.", "chips": "tool|deterministic|testable"},
        {"title": "Grounding", "body": "The model reasons over returned facts instead of inventing them.", "chips": "facts|least privilege"},
    ])
    '''


def primitives_agent_cells() -> list[dict[str, Any]]:
    make_agent = r'''
    # Primitive: Chat-client-backed agent
    from agent_framework.ollama import OllamaChatClient


    def make_agent(spec: AgentSpec, *, tools: list[object] | None = None):
        """Create an instruction-led local agent. Construction is cheap; model calls happen on run."""

        client = OllamaChatClient(host=DEFAULT_HOST, model=DEFAULT_MODEL)
        return client.as_agent(
            name=spec.name,
            description=spec.description,
            instructions=f"You are {spec.name}. {spec.instructions}",
            tools=tools or None,
            default_options={"temperature": 0.0, "max_tokens": SCENARIO.max_tokens, "think": False},
            require_per_service_call_history_persistence=True,
        )
    '''

    grants = r'''
    TOOL_GRANTS = {
        "PrimitiveMapAgent": [lookup_primitive_fact],
        "AgentRuntimeAgent": [lookup_primitive_fact, draft_enablement_check],
    }
    AGENT_BLUEPRINTS = [
        {"title": spec.name, "body": spec.description, "chips": "agent|instructions" + ("|function tools" if TOOL_GRANTS.get(spec.name) else "")}
        for spec in SCENARIO.agents
    ]
    render_cards(AGENT_BLUEPRINTS)
    print("make_agent(spec) is ready. The notebook delays real model calls until RUN_LIVE_AGENT is enabled.")
    '''

    return (
        teach(
            "make_agent",
            PRIMITIVE,
            "`client.as_agent(...)` turns an `OllamaChatClient` plus role instructions and "
            "granted tools into an agent -- the same factory call every scenario notebook uses. "
            "Construction is cheap and offline; the model is only contacted later, on `run`, "
            "which is why this cell executes instantly even with Ollama stopped.",
            make_agent,
        )
        + teach(
            "Tool grants",
            SUPPORT,
            "A plain lookup table declaring which function tools each agent may call. This is "
            "least-privilege wiring: an agent can only invoke what its spec grants, so a "
            "compromised or confused prompt cannot reach tools outside its role. Not framework "
            "surface, but a habit worth copying into production systems.",
            grants,
        )
    )


def primitives_session_cell() -> str:
    return r'''
    # Primitive: session or thread state
    SESSION_TURNS: dict[str, list[str]] = {}
    MAX_TURNS = 6


    def record_turn(session_id: str, role: str, text: str) -> list[str]:
        turns = SESSION_TURNS.setdefault(session_id, [])
        turns.append(f"{role}: {text}")
        del turns[: max(0, len(turns) - MAX_TURNS)]
        return turns


    record_turn("demo-session", "user", "Explain workflow routing.")
    record_turn("demo-session", "assistant", "Use WorkflowContext state plus code-defined router decisions.")
    render_transcript("\n".join(SESSION_TURNS["demo-session"]))
    print("Session state is explicit here; production agents can use framework-supported thread/history providers.")
    '''


def primitives_run_stream_cell() -> str:
    return r'''
    # Primitive: run and stream
    async def run_live_agent_once() -> None:
        agent = make_agent(SCENARIO.agents[0], tools=TOOL_GRANTS.get("PrimitiveMapAgent"))
        result = await agent.run("Return a six-bullet primitive checklist for this lab.")
        render_transcript(result.text or str(result))


    async def stream_live_agent_once() -> None:
        agent = make_agent(SCENARIO.agents[1], tools=TOOL_GRANTS.get("AgentRuntimeAgent"))
        chunks: list[str] = []
        async for update in agent.run("Explain function tools in one short paragraph.", stream=True):
            if getattr(update, "text", None):
                chunks.append(update.text)
        render_transcript("".join(chunks))


    if RUN_LIVE_AGENT:
        await run_live_agent_once()
        await stream_live_agent_once()
    else:
        render_trace([
            {"stage": "agent.run", "detail": "guarded off"},
            {"stage": "agent.run(..., stream=True)", "detail": "guarded off"},
        ])
    '''


def primitives_mcp_cell() -> str:
    return r'''
    # Primitive: MCPStdioTool
    from agent_framework import MCPStdioTool


    def describe_local_mcp_tool() -> dict[str, object]:
        return {
            "class": "MCPStdioTool",
            "command": "python",
            "args": ["-m", "sample_mcp_server"],
            "approval_mode": "never_require",
            "allowed_tools": ["lookup_primitive_fact"],
        }


    # Demo (offline): show the safe tool envelope rather than starting a subprocess.
    pprint(describe_local_mcp_tool())
    render_cards([
        {"title": "MCPStdioTool", "body": "Launches a local MCP server and exposes only approved tools.", "chips": "MCP|stdio|least privilege"},
        {"title": "Excluded here", "body": "Hosted MCP requires provider-side configuration, so this lab shows local MCP shape.", "chips": "local sample"},
    ])
    '''


def primitives_a2a_cell() -> str:
    return r'''
    # Primitive: A2AAgent
    from agent_framework.a2a import A2AAgent


    def make_remote_peer_reference() -> dict[str, str]:
        url = os.getenv("A2A_PARTNER_BASE_URL", "http://localhost:8765").rstrip("/") + "/primitive-peer"
        return {"class": "A2AAgent", "name": "PrimitivePeerAgent", "url": url}


    # Demo (offline): represent the remote seat without requiring a running server.
    pprint(make_remote_peer_reference())
    render_cards([
        {"title": "A2AAgent", "body": "A local proxy for a remote peer agent with its own card and runtime.", "chips": "A2A|remote agent"},
        {"title": "When to use", "body": "Use when another team owns the agent and you only orchestrate its seat.", "chips": "boundary|protocol"},
    ])
    '''


def primitives_workflow_cells() -> list[dict[str, Any]]:
    imports_and_messages = r'''
    # Primitive: Executor, @handler, WorkflowContext, and Message routing
    import re
    from typing import Never

    from agent_framework import (
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        Executor,
        Message,
        WorkflowBuilder,
        WorkflowContext,
        handler,
    )

    TRANSCRIPT_KEY = "primitive_transcript"


    def make_request(text: str) -> AgentExecutorRequest:
        return AgentExecutorRequest(messages=[Message(role="user", contents=[text])])


    def response_text(response: AgentExecutorResponse) -> str:
        agent_response = getattr(response, "agent_response", None)
        return (getattr(agent_response, "text", None) or "").strip()
    '''

    dispatch_executor = r'''
    class PromptDispatchExecutor(Executor):
        @handler
        async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            ctx.set_state("prompt", prompt)
            ctx.set_state(TRANSCRIPT_KEY, [])
            await ctx.send_message(make_request(prompt))
    '''

    output_executor = r'''
    class PrimitiveOutputExecutor(Executor):
        @handler
        async def finish(self, response: AgentExecutorResponse, ctx: WorkflowContext[Never, str]) -> None:
            transcript = list(ctx.get_state(TRANSCRIPT_KEY) or [])
            transcript.append(response_text(response))
            await ctx.yield_output("\n\n".join(transcript))


    # Demo (offline): the custom executors define graph behavior; agents fill in model work.
    render_trace([
        {"stage": "Executor", "detail": "a code node in the graph"},
        {"stage": "@handler", "detail": "typed method that receives messages"},
        {"stage": "WorkflowContext", "detail": "state, sends, target routing, outputs"},
    ])
    '''

    return (
        teach(
            "Workflow imports and message helpers",
            PRIMITIVE,
            "Imports the workflow primitives -- `Executor`, `WorkflowBuilder`, `WorkflowContext`, "
            "`AgentExecutor`, `@handler` -- and the request/response helpers that wrap plain text "
            "into an `AgentExecutorRequest` and back. Every executor below extends exactly these "
            "building blocks; this is the framework surface the whole workflow half of the lab "
            "stands on.",
            imports_and_messages,
        )
        + teach(
            "PromptDispatchExecutor",
            PRIMITIVE,
            "An `Executor` whose `@handler` seeds workflow state and `send_message`s the first "
            "request -- the entry node of a graph. The `@handler` decorator plus the typed "
            "signature is the whole registration mechanism: the framework reads the types to know "
            "which messages this node receives and what it may emit.",
            dispatch_executor,
        )
        + teach(
            "PrimitiveOutputExecutor",
            PRIMITIVE,
            "The terminal `Executor`: its handler calls `ctx.yield_output(...)` with the joined "
            "transcript, and that value becomes the workflow's result. Yielding instead of "
            "sending is how a graph node declares the run finished -- every pattern in this repo "
            "terminates this way.",
            output_executor,
        )
    )


def primitives_agent_executor_cell() -> str:
    return r'''
    # Primitive: AgentExecutor
    def slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


    def build_agent_executor(spec: AgentSpec, *, tools: list[object] | None = None) -> AgentExecutor:
        agent = make_agent(spec, tools=tools)
        return AgentExecutor(agent, id=slug(spec.name))


    EXECUTOR_IDS = [slug(spec.name) for spec in SCENARIO.agents]
    render_cards([
        {"title": "AgentExecutor", "body": "Wraps an agent so WorkflowBuilder can route messages to it.", "chips": "agent|workflow node"},
        {"title": "Stable ids", "body": ", ".join(EXECUTOR_IDS[:3]) + " ...", "chips": "observability|routing"},
    ])
    '''


def primitives_sequential_graph_cell() -> str:
    return r'''
    # Primitive: WorkflowBuilder graph
    class StageGateExecutor(Executor):
        def __init__(self, id: str, *, stage_name: str) -> None:
            super().__init__(id=id)
            self._stage_name = stage_name

        @handler
        async def gate(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
            transcript = list(ctx.get_state(TRANSCRIPT_KEY) or [])
            transcript.append(f"[{self._stage_name}] {response_text(response)}")
            ctx.set_state(TRANSCRIPT_KEY, transcript)
            prompt = ctx.get_state("prompt") or ""
            await ctx.send_message(make_request(prompt + "\n\nWork so far:\n" + "\n".join(transcript)))


    def build_workflow(scenario: ScenarioSpec):
        dispatch = PromptDispatchExecutor(id="dispatch")
        output = PrimitiveOutputExecutor(id="final_output")
        agents = [build_agent_executor(spec, tools=TOOL_GRANTS.get(spec.name)) for spec in scenario.agents]
        builder = WorkflowBuilder(start_executor=dispatch, output_from=[output])
        builder.add_edge(dispatch, agents[0])
        for index in range(len(agents) - 1):
            gate = StageGateExecutor(id=f"gate_{index}", stage_name=scenario.agents[index].name)
            builder.add_edge(agents[index], gate)
            builder.add_edge(gate, agents[index + 1])
        builder.add_edge(agents[-1], output)
        return builder.build()


    # Demo (offline): describe the graph without calling a model.
    render_trace([
        {"stage": "dispatch", "detail": "normalizes prompt"},
        {"stage": "agent nodes", "detail": "AgentExecutor wraps each role"},
        {"stage": "stage gates", "detail": "carry transcript via WorkflowContext"},
        {"stage": "final output", "detail": "yields readable text"},
    ])
    '''


def primitives_handoff_cell() -> str:
    return r'''
    # Primitive: code-validated handoff routing
    class HandoffRouterExecutor(Executor):
        def __init__(self, id: str, *, routes: dict[str, tuple[str, ...]], default_route: str) -> None:
            super().__init__(id=id)
            self._routes = routes
            self._default_route = default_route

        def choose(self, text: str) -> str:
            lowered = text.lower()
            if "route:" in lowered:
                candidate = lowered.rsplit("route:", 1)[1].strip().split()[0]
                if candidate in self._routes:
                    return candidate
            scored = sorted(
                ((sum(keyword in lowered for keyword in keywords), route) for route, keywords in self._routes.items()),
                reverse=True,
            )
            return scored[0][1] if scored and scored[0][0] else self._default_route


    router = HandoffRouterExecutor(
        id="router",
        routes={"tooling": ("tool", "mcp", "function"), "workflow": ("workflow", "executor", "graph")},
        default_route="workflow",
    )
    # Demo (offline): model text can suggest, but code validates.
    print(router.choose("Need MCP and function tool guidance. ROUTE: tooling"))
    '''


def primitives_concurrent_cell() -> str:
    return r'''
    # Primitive: fan-out and fan-in
    class ConcurrentAggregatorExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names

        def label_outputs(self, texts: list[str]) -> str:
            return "\n\n".join(f"[{name}]\n{text}" for name, text in zip(self._agent_names, texts))


    class ConcurrentSynthesisGateExecutor(Executor):
        def __init__(self, id: str, *, agent_names: list[str]) -> None:
            super().__init__(id=id)
            self._agent_names = agent_names


    aggregator = ConcurrentAggregatorExecutor(id="aggregator", agent_names=["AgentRuntimeAgent", "WorkflowGraphAgent"])
    # Demo (offline): labelled fan-in keeps parallel evidence attributable.
    render_transcript(aggregator.label_outputs(["Agent runtime facts", "Workflow graph facts"]))
    '''


def primitives_group_chat_cell() -> str:
    return r'''
    # Primitive: GroupChatBuilder
    from agent_framework.orchestrations import GroupChatBuilder, GroupChatState


    def round_robin_selector(state: GroupChatState) -> str:
        participant_names = list(state.participants.keys())
        return participant_names[state.current_round % len(participant_names)]


    def termination_condition(messages: list[Any]) -> bool:
        assistant = [message for message in messages if getattr(message, "role", None) == "assistant"]
        return bool(assistant) and "final primitive map" in (getattr(assistant[-1], "text", "") or "").lower()


    render_cards([
        {"title": "GroupChatBuilder", "body": "Coordinates a visible multi-agent discussion.", "chips": "selector|termination"},
        {"title": "Selector", "body": "A function chooses who speaks next.", "chips": "code-defined"},
        {"title": "Termination", "body": "A function decides when the discussion is done.", "chips": "bounded"},
    ])
    '''


def primitives_magentic_cell() -> str:
    return r'''
    # Primitive: MagenticBuilder
    from agent_framework.orchestrations import MagenticBuilder

    MAGENTIC_LIMITS = {"max_round_count": 10, "max_stall_count": 3, "max_reset_count": 2}
    render_cards([
        {"title": "MagenticBuilder", "body": "A manager agent plans, delegates, observes progress, and replans.", "chips": "manager|dynamic"},
        {"title": "Ledger limits", "body": json.dumps(MAGENTIC_LIMITS), "chips": "bounded|observable"},
    ])
    '''


def primitives_hosting_cell(project: dict[str, str]) -> str:
    return f'''
    # Primitive: hosting boundary
    HOSTING_SHAPES = {{
        "ResponsesHostServer": "Expose one selected workflow through OpenAI-compatible /responses.",
        "InvocationAgentServerHost": "Expose a custom /invocations contract where each request can choose a scenario.",
        "current notebook boundary": "{project['api_boundary']}",
    }}
    pprint(HOSTING_SHAPES)
    render_cards([
        {{"title": "Responses", "body": "Best for chat clients and OpenAI-compatible tooling.", "chips": "standard endpoint"}},
        {{"title": "Invocations", "body": "Best for jobs, webhooks, CI, and custom payloads.", "chips": "custom contract"}},
    ])
    '''


def primitives_observability_cell() -> str:
    return r'''
    # Primitive: observability
    def workflow_result_to_text(events: Any) -> str:
        if hasattr(events, "get_outputs"):
            outputs = events.get_outputs()
            if outputs:
                return "\n".join(str(output) for output in outputs)
        return str(events)


    OBSERVABILITY_CHECKLIST = [
        {"stage": "name every executor", "detail": "ids make traces readable"},
        {"stage": "label fan-in outputs", "detail": "parallel findings stay attributable"},
        {"stage": "record route source", "detail": "model-directive vs keyword fallback"},
        {"stage": "bound dynamic loops", "detail": "max rounds, stalls, and resets"},
        {"stage": "render transcript", "detail": "teach from the actual conversation, not a summary"},
    ]
    render_trace(OBSERVABILITY_CHECKLIST)
    render_transcript("Observability is a design primitive: name nodes, expose state, label outputs, and bound loops.")
    '''


def primitives_flow_diagram_cell(project: dict[str, str]) -> str:
    api_boundary = project["api_boundary"]
    api_label = api_boundary.replace('"', "'")
    return f'''
    # Flow Diagram
    def _label(value: str) -> str:
        return value.replace('"', "'")


    def _mermaid_image_url(mermaid: str) -> str:
        encoded = base64.urlsafe_b64encode(mermaid.encode("utf-8")).decode("ascii").rstrip("=")
        return f"https://mermaid.ink/img/{{encoded}}"


    def display_scenario_flow() -> str:
        mermaid = "\\n".join([
            "%%{{init: {{'theme': 'neutral'}}}}%%",
            "flowchart LR",
            "    input[Request] --> messages[Message]",
            "    messages --> agent[Chat-client-backed agent]",
            "    agent --> tools[Function tools]",
            "    agent -. local tools .-> mcp[MCPStdioTool]",
            "    agent -. remote peer .-> a2a[A2AAgent]",
            "    agent --> executor[AgentExecutor]",
            "    executor --> workflow[WorkflowBuilder graph]",
            "    workflow --> routing[Routing / fan-out / fan-in]",
            "    workflow --> group[GroupChatBuilder]",
            "    workflow --> magentic[MagenticBuilder]",
            "    workflow --> host[{api_label}]",
            "    workflow --> trace[Trace + transcript]",
        ])
        display(HTML(
            "<figure style='margin:0'>"
            f"<img src='{{html.escape(_mermaid_image_url(mermaid))}}' alt='Agent Framework primitive flow' "
            "style='max-width:100%; height:auto;' />"
            "<figcaption style='font-size:.9em; color:#475569'>Agent Framework primitive flow</figcaption>"
            "</figure>"
        ))
        return mermaid


    flow_diagram = display_scenario_flow()
    print(flow_diagram)
    '''


def primitives_post_markdown() -> str:
    return """
    ## What to Inspect

    Check that each primitive has a visible boundary:

    - Messages are data, not orchestration.
    - Agents own model calls and tool access.
    - Tools own deterministic external action.
    - MCP and A2A are protocol boundaries, not prompt tricks.
    - Executors own code-defined workflow behavior.
    - WorkflowContext owns graph state and message sends.
    - Builders own graph shape and dynamic coordination.
    - Hosting owns the client contract.
    - Observability is designed into names, labels, traces, and transcripts.

    ## Experiments

    - Set `RUN_LIVE_AGENT=1` and rerun the run/stream cell after Ollama is available.
    - Add one more function tool and grant it to only one agent.
    - Change the handoff router sample text and watch the route decision move.
    - Add a third fan-out lane to the aggregator demo.
    - Decide which excluded hosted primitive you would add first in a cloud-backed version.
    """


def build_primitives_notebook(project: dict[str, str], scenario: Any) -> dict[str, Any]:
    cells = [
        md(primitives_title_markdown(project, scenario)),
        *primitives_environment_cells(),
        md(primitives_overview_markdown()),
        md(primitives_pattern_comparison_markdown()),
        *primitives_scenario_cells(project, scenario),
        md("## Primitive: Message\n\nMessages are the typed boundary between user, system, assistant, agents, and workflow nodes. Every hop in every orchestration -- a prompt entering, an agent replying, a gate forwarding -- is one of these shapes, so learning to read a message is learning to read a run. The cell below builds each role by hand so you can see exactly what agents exchange."),
        code(primitives_message_cell()),
        md("## Primitive: Function Tool\n\nFunction tools are the smallest useful grounding mechanism: a callable with a narrow, testable contract. The agent decides when to call and with what arguments; your code decides what happens -- that split is the whole tool-use story. Notice the fixtures are deterministic, so a tool call here always returns the same answer."),
        code(primitives_function_tool_cell()),
        md("## Primitive: Agent\n\nInstruction-led agents combine a chat client, role instructions, optional tools, runtime options, and a run interface. There is no hidden magic: an agent is configuration around a model call, which is why the factory below can build a whole roster in a loop. Everything the orchestration patterns coordinate is instances of this primitive."),
        *primitives_agent_cells(),
        md("## Primitive: Session Or Thread State\n\nState is explicit. An agent remembers nothing between runs unless you hand history back to it, so multi-turn behavior is always a choice you make, not a default you inherit. Keep state bounded and visible in local samples; move to provider or framework history stores when a real application needs durability."),
        code(primitives_session_cell()),
        md("## Primitive: Run And Stream\n\nNon-streaming returns one final response; streaming exposes incremental updates as they are generated. The choice is about your caller, not the model -- a webhook wants the finished answer, a chat UI wants tokens as they arrive. The offline demo below fakes the stream so you can see the event shapes without a live model."),
        code(primitives_run_stream_cell()),
        md("## Primitive: MCP\n\nMCP connects an agent to tools through a protocol instead of in-process function references -- the tool server can be a different process, language, or team, and the agent's contract does not change. Local stdio MCP is the right variant for this teaching repo: no network, no credentials, fully reproducible. Scenarios 11-16 and 19-23 run entire businesses on this primitive."),
        code(primitives_mcp_cell()),
        md("## Primitive: A2A\n\nA2A connects an orchestration to a peer agent owned by another runtime or organization: discovery via an agent card, calls via JSON-RPC, no shared code. Where MCP grounds an agent in tools, A2A seats a whole other agent at your table. Scenario 17 runs a group chat where two seats live behind this protocol."),
        code(primitives_a2a_cell()),
        md("## Primitive: Workflow Executor\n\nCustom executors make business logic explicit and testable inside the graph: subclass `Executor`, decorate an async method with `@handler`, and the typed signature declares what the node consumes and emits. Every gate, router, and aggregator in this repo is this one primitive specialized -- master it and the pattern machinery reads itself."),
        *primitives_workflow_cells(),
        md("## Primitive: AgentExecutor\n\nAgentExecutor is the bridge from an agent to a workflow node: it gives the agent a graph id, receives `AgentExecutorRequest`s, runs the agent, and emits its response into the graph. This is how the agent world (instructions, tools) and the workflow world (edges, state) stay separate concerns that compose."),
        code(primitives_agent_executor_cell()),
        md("## Primitive: WorkflowBuilder\n\nWorkflowBuilder turns executors and agents into a deterministic graph: `start_executor` and `output_from` mark the ends, `add_edge` wires the middle. The topology is fixed before anything runs -- the sequential pipeline below is code deciding order, with no model in the loop."),
        code(primitives_sequential_graph_cell()),
        md("## Primitive: Handoff Routing\n\nA router lets the model suggest ownership while code validates the allowed route -- the ROUTE directive is honored only if it names a real specialist, with keyword scoring as the fallback. This suggest-then-validate split is the safest way to let a model steer control flow. The demo exercises both paths offline."),
        code(primitives_handoff_cell()),
        md("## Primitive: Fan-Out And Fan-In\n\nConcurrent work is useful only when aggregation keeps each lane attributable. `add_fan_out_edges` starts every lane at once; `add_fan_in_edges` delivers all responses to one collector as a single list -- and labelling each response by its lane is what keeps the combined output auditable rather than a blur."),
        code(primitives_concurrent_cell()),
        md("## Primitive: Group Chat\n\nGroup chat is a visible discussion with code-defined speaker selection and termination: a selector chooses who talks next, and a termination closure -- checked only at cycle boundaries so the closer always speaks last -- decides when the debate has earned its verdict. The transcript is the deliverable."),
        code(primitives_group_chat_cell()),
        md("## Primitive: Magentic\n\nMagentic coordination uses a manager agent plus bounded progress-ledger behavior: the manager plans, delegates, watches for stalls, and replans, while `max_round_count`, `max_stall_count`, and `max_reset_count` keep the loop finite. It is the most powerful and most expensive pattern here -- the bounds are the difference between adaptive and runaway."),
        code(primitives_magentic_cell()),
        md("## Primitive: Hosting\n\nThe same workflow can sit behind different API contracts -- this repo hosts identical scenarios behind an OpenAI-compatible Responses API and a custom Invocations API. Orchestration choice and API-boundary choice are independent decisions; conflating them is the most common architecture mistake this repo exists to untangle."),
        code(primitives_hosting_cell(project)),
        md("## Primitive: Observability\n\nGood agent systems are inspectable by construction: labelled transcripts, route-source headers, intermediate outputs, and decision logs are built into the executors in this repo, not bolted on afterward. When an orchestration misbehaves, these artifacts -- not rerunning and hoping -- are how you find out why."),
        code(primitives_observability_cell()),
        md("## Flow Diagram\n\nThis diagram connects the primitives from request to hosted, observable workflow -- messages enter, agents and executors coordinate, tools and peers ground the work, and outputs surface with attribution. If you can trace this picture, you can read any scenario notebook in the repo."),
        code(primitives_flow_diagram_cell(project)),
        md(primitives_post_markdown()),
    ]
    add_cell_ids(cells, scenario.id)
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_notebook(project: dict[str, str], scenario: Any) -> dict[str, Any]:
    if scenario.id == PRIMITIVES_SCENARIO_ID:
        return build_primitives_notebook(project, scenario)

    data = scenario_data(scenario, project["sample_attr"])
    server = scenario_mcp_server(scenario)
    cells = [md(title_markdown(project, scenario))]
    cells.extend(environment_cells())
    cells.append(md(concept_markdown(project, scenario)))
    cells.append(md(pattern_deep_dive_markdown(project, scenario)))
    if server:
        cells.append(md(mcp_markdown(server)))
        if server == "quote_to_cash_context":
            cells.extend(teach(
                "Domain fixtures",
                SUPPORT,
                "The embedded quote-to-cash records the tools read: two opportunity triggers (one "
                "ready, one blocked), two customer profiles with different contract terms, a "
                "small SKU catalog with an incompatibility and an availability wrinkle, and the "
                "legal thresholds. The teaching tensions live in this data -- the 25 percent "
                "discount crossing the legal threshold is a fixture fact, not a prompt trick. "
                "Inlined so the notebook stays self-contained; no MCP server, no Agent Framework "
                "surface.",
                quote_to_cash_fixtures_cell(),
            ))
            cells.extend(teach(
                "Domain tools",
                SUPPORT,
                "Plain callables over the fixtures, registered in `MCP_TOOL_FUNCTIONS` so "
                "`make_agent` can grant them to agents by name -- each returns the same "
                "deterministic dict every run. In production these functions would sit behind a "
                "FastMCP stdio server attached via `MCPStdioTool`; inlining them keeps the "
                "notebook runnable anywhere while preserving the exact tool contract the agents "
                "see. The cell ends with a real call so you see a grounded result before any "
                "agent does.",
                quote_to_cash_tools_cell('crm_get_quote_trigger("OPP-5001")'),
            ))
        else:
            demo_call = ENTERPRISE_DEMO_CALLS.get(scenario.id, 'search_policy("security review")')
            cells.extend(teach(
                "Domain fixtures",
                SUPPORT,
                "The embedded enterprise records the tools read: vendors, alerts, claims, "
                "facilities, loan applications, acquisition targets, disputes, and the policy "
                "catalog and playbooks that govern them. Each record carries an engineered "
                "tension -- an expired review, a conflicting policy, a fraud signal tied with a "
                "merchant-error signal -- that this scenario's agents are supposed to surface. "
                "Inlined so the notebook stays self-contained; no MCP server, no Agent Framework "
                "surface.",
                enterprise_fixtures_cell(),
            ))
            cells.extend(teach(
                "Domain tools",
                SUPPORT,
                "Plain callables over the fixtures, registered in `MCP_TOOL_FUNCTIONS` so "
                "`make_agent` can grant them by name: record lookups, keyword policy search, a "
                "deterministic priority score, playbook steps, and a write-shaped decision log "
                "that never persists. In production these would be a FastMCP stdio server "
                "attached via `MCPStdioTool`; inlining preserves the exact tool contract while "
                "keeping the notebook self-contained. The cell ends with this scenario's "
                "grounding call so you see a real tool result before any agent runs.",
                enterprise_tools_cell(demo_call),
            ))
    if scenario_uses_a2a(scenario):
        cells.append(md(a2a_markdown()))
        cells.extend(teach(
            "Partner facts and behavior",
            SUPPORT,
            "The partner data plus a deterministic `partner_reply` that selects facts based on "
            "the question asked -- the behavior each remote seat will serve. No LLM, no network "
            "yet. Read the fixtures closely: the certification expiring mid-window and the open "
            "compliance finding are the facts the whole scenario turns on, and they exist only on "
            "this side of the A2A boundary.",
            a2a_fixtures_cell(),
        ))
        cells.extend(teach(
            "Host the partner agents",
            PRIMITIVE,
            "The hosting side of A2A: each partner behavior is wrapped in a `BaseAgent`, exposed "
            "through an `A2AExecutor`, given an agent card at `/.well-known/agent-card.json`, and "
            "served over HTTP from an in-process server. After this cell there are real agents "
            "listening on localhost that any A2A client -- this notebook or another "
            "organization's runtime -- could discover and call.",
            a2a_server_cell(),
        ))
        cells.extend(teach(
            "Discover agent cards",
            SUPPORT,
            "Fetches each partner's `agent-card.json` over plain HTTP -- the discovery step an "
            "A2A client performs before talking to a peer. The card is the protocol's public "
            "contract: name, description, capabilities, endpoint. Notice everything the client "
            "does not need: the partner's code, model, or prompts.",
            a2a_discovery_cell(),
        ))
        cells.extend(teach(
            "One A2A round-trip",
            PRIMITIVE,
            "`A2AAgent` connects to a remote peer by URL and `run`s a single message -- the "
            "client side of the protocol, exercised once before any orchestration depends on it. "
            "The returned object behaves like a normal Agent Framework agent, which is the "
            "punchline: after this cell, remote seats and local seats are interchangeable to the "
            "group chat.",
            a2a_client_cell(),
        ))
    cells.extend(scenario_cells(project, data))
    cells.extend(agent_factory_cells())
    cells.extend(plumbing_cells())
    cells.extend(pattern_machinery_cells(scenario.pattern))
    cells.extend(build_cells(scenario.pattern))
    cells.append(md(flow_diagram_markdown(project, scenario)))
    cells.append(code(diagram_cell(project, scenario.pattern, scenario.id.startswith("scenario-16-quote-to-cash"))))
    cells.extend(teach(
        "Read the run output",
        SUPPORT,
        "Utilities that unpack a finished run: `result.get_outputs()` returns the workflow's "
        "yielded outputs, and `get_intermediate_outputs()` exposes per-participant turns where "
        "the orchestration surfaces them (group chat and magentic). Everything else is string "
        "parsing that feeds `render_transcript`, so the color-coded turns you see below are "
        "exactly what the executors yielded -- those two calls are the only Agent Framework "
        "touchpoints.",
        results_cell(scenario.pattern == "group-chat"),
    ))
    cells.append(md(live_run_markdown(scenario)))
    cells.append(code(live_run_cell()))
    cells.append(md(post_run_markdown(scenario)))
    cells.append(md(experiments_markdown(project, scenario)))
    add_cell_ids(cells, scenario.id)
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    for project in PROJECTS:
        scenarios = load_scenarios(project)
        paths = notebook_paths_by_id(project, scenarios)
        for scenario in scenarios:
            notebook = build_notebook(project, scenario)
            path = paths[scenario.id]
            path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
