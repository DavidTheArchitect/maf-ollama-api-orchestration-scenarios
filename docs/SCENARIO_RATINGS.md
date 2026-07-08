# Scenario Ratings — Microsoft Agent Framework Instructor Review

> **Re-rated after the improvement pass (2026-07-04).** The structural fixes
> recommended by this review have been implemented: model-directed handoff
> routing with curated keywords and fixed finishers (#6), post-fan-in
> concurrent synthesizers (#7), per-scenario group-chat termination with the
> synthesizer closing every cycle (#8), and artifact-dependent onboarding
> stages. Current ratings, verified by both offline test suites:
>
> | # | Scenario | Before | After | | # | Scenario | Before | After |
> | --- | --- | --- | --- | --- | --- | --- | --- | --- |
> | 01 | sequential-release-readiness | 9 | **9** | | 11 | sequential-procurement-approval | 9 | **9** |
> | 02 | concurrent-pr-review | 9 | **9** | | 12 | concurrent-security-alert-enrichment | 6 | **8** |
> | 03 | handoff-support-triage | 7 | **8** | | 13 | handoff-claims-exception-routing | 7 | **9** |
> | 04 | group-chat-launch-council | 7 | **8** | | 14 | group-chat-policy-exception-board | 8 | **9** |
> | 05 | magentic-incident-response | 9 | **9** | | 15 | magentic-business-continuity-drill | 8 | **8** |
> | 06 | sequential-employee-onboarding | 7 | **8** | | 16a | quote-to-cash sequential | 9 | **9** |
> | 07 | concurrent-vendor-risk-assessment | 9 | **9** | | 16b | quote-to-cash concurrent | 6 | **8** |
> | 08 | handoff-customer-entitlement | 6\* | **8** | | 16c | quote-to-cash handoff | 5 | **8** |
> | 09 | group-chat-quarterly-planning | 7 | **8** | | 16d | quote-to-cash group chat | 6 | **8** |
> | 10 | magentic-supply-chain-disruption | 8 | **8** | | 16e | quote-to-cash magentic | 8 | **8** |
>
> Average: **7.6 → 8.4**. No scenario below 8. (\*Scenario 08 was lowered from
> 7 to 6 in a second evaluation pass after empirically running the old keyword
> router: the auto-generated keyword `customer` biased routing toward the
> comms agent; the curated keywords in #6 removed that bias.)
>
> **Polish pass (PRs #13-#15).** A second improvement pass implemented
> `SCENARIO_POLISH_PLAN.md`: cell-per-concept notebooks with offline demos and
> teaching visuals, a logic audit encoded as test invariants, deeper domain
> fixtures (working material in starters, decision pressure in enterprise
> scenarios, engineered wrinkles in every MCP fixture set, and a 25% discount
> crossing the legal threshold in quote-to-cash), and scenario-specific
> inspect/experiment spotlights. Ratings raised where the added depth removed
> the remaining weakness: 10 (8 to 9, capped-budget tradeoffs), 12 (8 to 9,
> stale-rotation wrinkle plus synthesis stage), 15 (8 to 9, contrast facility
> forces prioritization), 16d and 16e (8 to 9, the discount gives the debate
> and the delegation real stakes). Average: **8.4 to 8.65**.
>
> **Scenario 17 (added with `SCENARIO_17_A2A_PLAN.md`).**
> `group-chat-partner-launch-review` -- Group chat + A2A: **9/10**. Two council
> seats are remote peer agents behind real agent cards and JSON-RPC endpoints
> served by a bundled deterministic A2A server; the group-chat orchestration
> from PR #8 is reused verbatim, which is the lesson. The offline protocol
> tests exercise genuine A2A round-trips with zero LLM calls, and the notebook
> walks fixtures, hosting, card discovery, and a direct client round-trip
> before any orchestration exists. Deduction: the deterministic partners reply
> with their full fact sheet regardless of the question; the `--ollama` mode
> covers the fully dynamic case.
>
> **Code-review pass (`SCENARIO_CODE_REVIEW.md`, PRs #17-#18).** A combined
> clean-code and scenario-quality review fixed two real API-layer bugs (a
> swallowed-TypeError server fallback and an unbounded session cache),
> restructured the output-extraction helpers, made the documented Ollama
> defaults truthful, and closed the last per-scenario deductions: sequential
> stage gates now instruct each stage to add rather than repeat (01),
> concurrent fan-in labels responses by executor id instead of list position
> (02), and the Scenario 17 partner agents answer the question they were
> asked while staying deterministic. With those deductions gone, 01, 02, and
> 17 rise to **10/10**. Average: **8.67 to 8.81**.
>
> The review below is the original assessment that motivated the changes; its
> "Cross-Cutting Recommendations" have all been implemented.

An instructor's original review of the first twenty learning scenarios shared by
`responses-api-scenarios/` and `invocations-api-scenarios/`. Each scenario is
rated **1–10 as a teaching vehicle for its orchestration pattern**, based on
inspection of the scenario modules, the shared workflow builders
(`workflows.py`), the custom executors (`executors.py`), the two local MCP
servers, and the companion notebooks. Ratings apply to the scenario as a
learning unit across both API packages (the Invocations variants differ only in
framing and, for scenarios 01–05, slightly in agent rosters).

## Rubric

| Dimension | What was assessed |
| --- | --- |
| Pattern fit | Does the business story genuinely call for this orchestration pattern? |
| MAF feature coverage | Does it exercise real framework machinery (`WorkflowBuilder`, `AgentExecutor`, `GroupChatBuilder`, `MagenticBuilder`, `MCPStdioTool`)? |
| Instructional clarity | Can a learner see the pattern in the code and the output? |
| Realism | Would a practitioner recognize the workflow? |
| Structural soundness | Does the wired graph actually deliver what the scenario's learning goal promises? |

## Summary Table

| # | Scenario | Pattern | Rating |
| --- | --- | --- | --- |
| 01 | `sequential-release-readiness` | Sequential | **9/10** |
| 02 | `concurrent-pr-review` | Concurrent | **9/10** |
| 03 | `handoff-support-triage` | Handoff | **7/10** |
| 04 | `group-chat-launch-council` | Group chat | **7/10** |
| 05 | `magentic-incident-response` | Magentic | **9/10** |
| 06 | `sequential-employee-onboarding` | Sequential | **7/10** |
| 07 | `concurrent-vendor-risk-assessment` | Concurrent | **9/10** |
| 08 | `handoff-customer-entitlement` | Handoff | **7/10** |
| 09 | `group-chat-quarterly-planning` | Group chat | **7/10** |
| 10 | `magentic-supply-chain-disruption` | Magentic | **8/10** |
| 11 | `sequential-procurement-approval` | Sequential + MCP | **9/10** |
| 12 | `concurrent-security-alert-enrichment` | Concurrent + MCP | **6/10** |
| 13 | `handoff-claims-exception-routing` | Handoff + MCP | **7/10** |
| 14 | `group-chat-policy-exception-board` | Group chat + MCP | **8/10** |
| 15 | `magentic-business-continuity-drill` | Magentic + MCP | **8/10** |
| 16a | `scenario-16-quote-to-cash-sequential` | Sequential + MCP | **9/10** |
| 16b | `scenario-16-quote-to-cash-concurrent` | Concurrent + MCP | **6/10** |
| 16c | `scenario-16-quote-to-cash-handoff` | Handoff + MCP | **5/10** |
| 16d | `scenario-16-quote-to-cash-group-chat` | Group chat + MCP | **6/10** |
| 16e | `scenario-16-quote-to-cash-magentic` | Magentic + MCP | **8/10** |

Average: **7.6/10**. The sequential and concurrent starters, the magentic
scenarios, and the MCP-grounded procurement pipeline are excellent teaching
material. The weak spots are structural: the handoff graph is a single-hop
keyword router, the group-chat termination condition is tailored to only one of
the four group-chat scenarios, and two of the quote-to-cash variants promise
behavior the wired graph cannot deliver.

---

## Software Delivery Scenarios (01–05)

### 01 — Sequential Release Readiness — 9/10

The archetypal first lesson. Five roles (scope → dependencies → risk → docs →
final editor) each genuinely transform the previous stage's output, so the
pattern's defining property — accumulation — is visible in the transcript. The
implementation is honest framework usage: an explicit `WorkflowBuilder` chain
of `AgentExecutor` nodes with `StageGateExecutor` gates that append to shared
`WorkflowContext` state and forward *"Original request + Work so far"*. The
Invocations variant sensibly reframes the same pipeline as a job
(intake → audit → classify → evidence → action plan). Only deduction: agent
instructions don't tell each stage which section of the carried transcript is
theirs to build on, so with a small local model stages occasionally re-answer
the whole prompt.

### 02 — Concurrent PR Review — 9/10

Near-perfect pattern fit: five reviewers (security, performance, tests,
maintainability, release risk) are truly independent, which is exactly the
precondition concurrent orchestration teaches. `add_fan_out_edges` /
`add_fan_in_edges` with a code-defined `ConcurrentAggregatorExecutor` shows
learners that aggregation can be deterministic code rather than another LLM
call. The labelled `[AgentName]` output makes the parallelism legible. Minor
nit: the aggregator matches names to responses by list index rather than by
executor id, which works but is a fragile idiom to teach.

### 03 — Handoff Support Triage — 7/10

A believable story (SSO + invoice export failure is deliberately ambiguous
across three specialists) and a clean graph: triage agent → code router → one
specialist → output. Two deductions. First, the "handoff" here is a
**keyword-scoring router in code** (`HandoffRouterExecutor.choose`), not the
framework's function-call handoff — yet `LEARNING_PATH.md` tells learners to
"look for function-call handoffs". Second, the route keywords are derived
mechanically from agent name + description (`_route_keywords`), which produces
noisy tokens like `authspecialistagent`, `handles`, and `problems` that appear
in several routes; ties resolve by dictionary order. The routing decision
recorded in `[routed to …]` output is good teaching; the mechanism deserves a
more honest label ("code-defined routing") or curated keyword lists per route.
The `EscalationCoordinatorAgent` is also unreachable as a *follow-up* — the
graph supports exactly one hop, so escalation only happens if triage text
happens to route there.

### 04 — Group Chat Launch Council — 7/10

A genuinely debatable question ("launch this week or hold?") with five
stakeholders arguing distinct incentives — good group-chat material, and the
custom `selection_func` + `termination_condition` on `GroupChatBuilder` are
exactly the right framework features to demonstrate. Deductions: the shared
`stop_after_council` terminator looks for "approved" + "recommendation", which
was written for scenario 14's board and rarely fires here, so this council
almost always just runs out its 7-message budget; and with round-robin over
five participants ending at message 7, the designated synthesizer
(`ReleaseNotesAgent`, slot 5) never gets the last word — the transcript ends
mid-rotation on the SRE.

### 05 — Magentic Incident Response — 9/10

Incident response is the canonical magentic use case: symptoms arrive
unordered, and which specialist should act next depends on what was just
learned. The scenario cleanly separates the `IncidentManagerAgent` (manager)
from five specialists and uses the real `MagenticBuilder` with
`max_round_count`, `max_stall_count`, and `max_reset_count` — learners see
ledger-driven planning and replanning rather than a scripted imitation. The
sample input plants three intertwined symptoms (export timeouts, delayed
reconciliation, rising tickets), giving the manager real material to plan
around. The only caveat is operational, not design: a 14B local model as
manager can stall, which is why the ledger limits matter — and the notebook
would benefit from saying so explicitly.

## Enterprise Workflow Scenarios (06–10)

### 06 — Sequential Employee Onboarding — 7/10

Relatable domain and clear per-department roles. The deduction is pattern fit:
HR, IT, security, and payroll onboarding tracks are largely *parallel* in real
enterprises — only the final `EnablementManagerAgent` synthesis genuinely
requires the previous outputs. Instructors should expect (and can productively
use) the question "why isn't this concurrent?"; the scenario itself doesn't
answer it, while scenario 11 shows what a genuinely order-dependent sequential
enterprise pipeline looks like.

### 07 — Concurrent Vendor Risk Assessment — 9/10

Textbook concurrent fit — security, privacy, legal, finance, and operations
really do assess a vendor independently and in parallel in real organizations,
so the pattern maps one-to-one onto practice. The single intake question with
five disjoint risk lenses produces clearly differentiated parallel outputs.
Together with 02 it cements the pattern; it loses a point only for being
structurally identical to 02 (no new framework surface is exercised).

### 08 — Handoff Customer Entitlement — 7/10

The strongest handoff *story* of the non-MCP set: "premium feature disappeared
after renewal" plausibly belongs to billing, contract, support, or engineering,
which is precisely when routing earns its keep. Same structural caveats as 03:
one-hop keyword routing in code, generated route keywords, and a
`CustomerSupportAgent` whose communication role reads like a follow-up step the
single-hop graph can't provide.

### 09 — Group Chat Quarterly Planning — 7/10

Good multi-stakeholder tension (revenue vs. product vs. support vs. finance)
and a `ChiefOfStaffAgent` chartered to drive convergence. Same mechanical
issues as 04: the termination phrase is borrowed from scenario 14, and the
round-robin/7-message combination means the Chief of Staff speaks once, at
turn 5, then the rotation wraps back to revenue and product — so the "operating
plan with owners and metrics" the learning goal promises is usually not the
final message.

### 10 — Magentic Supply Chain Disruption — 8/10

A strong open-ended planning problem spanning supplier, inventory,
manufacturing, customer, and finance dimensions — the breadth genuinely
requires delegation, and the manager/specialist split is clean. Slightly weaker
than 05 as a *first* magentic lesson because the five specialist reports are
more independent (closer to concurrent-with-a-manager); 05's interlocking
symptoms force more visible replanning.

## MCP Tool Scenarios (11–15)

The shared infrastructure here deserves separate praise: the
`enterprise-context` FastMCP stdio server is deterministic, credential-free,
write-free, and embedded in the package, and agents attach through
`MCPStdioTool` with per-agent `allowed_tools` — least-privilege tool exposure
demonstrated by construction, not by lecture. This is the right way to teach
MCP.

### 11 — Sequential Procurement Approval — 9/10

The best enterprise scenario in the repository. Every stage's tool grant maps
exactly to its job (intake gets record lookup; budget gets policy search +
priority scoring; the packet agent gets the playbook and the decision log), and
the fixture data is engineered to create a real finding — VENDOR-4471's
security review is *expired* against a policy requiring one under 12 months —
so tool grounding visibly changes the outcome instead of decorating it. The
`create_decision_log_entry` tool returning what it *would* write, with a
deterministic hash id, is an elegant way to teach action-shaped tools safely.

### 12 — Concurrent Security Alert Enrichment — 6/10

Four enrichment agents (identity, endpoint, network, data-loss) each pulling
their own facts about ALERT-2298 in parallel is a great concurrent-plus-MCP
lesson. The structural flaw: `IncidentSummaryAgent` is instructed to "combine
the independent perspectives into one incident summary," but in the concurrent
graph it runs *in parallel with* the enrichers and fans into the code
aggregator like everyone else — it can never see the perspectives it is told to
combine. Its output silently duplicates what `ConcurrentAggregatorExecutor`
already does. The fix is small (make it a post-aggregation stage, or cut it and
let the code aggregator be the lesson), and would take this to an 8.

### 13 — Handoff Claims Exception Routing — 7/10

The most defensible handoff of the set because the routing decision is
*tool-grounded*: the triage agent looks up CLAIM-88120 (over the auto-approval
threshold, one fraud signal) and scores it before routing, and the policy
catalog contains the exact routing rule (POL-CLM-09). That is the right lesson
— route on facts, not vibes. Still capped by the shared handoff mechanics: the
code router keyword-matches the triage *text*, and `CustomerCommsAgent` — whose
instructions assume a decision has already been made — is a routing *sibling*,
not a downstream step, so the promised customer communication usually never
happens.

### 14 — Group Chat Policy Exception Board — 8/10

The best group chat, because the machinery finally matches the story: this is
the one scenario the shared `stop_after_council` terminator was written for —
the `BoardChairAgent` is explicitly instructed to say "approved"/"denied" with
a recommendation, so learners can watch a semantic termination condition
actually fire instead of hitting the message cap. Four participants (not five)
also means the chair's slot in the rotation lands usefully. Risk, business
need, and compliance each ground their arguments in different tools, and the
fixture (90-day EU residency waiver vs. POL-GOV-03's compensating-control
requirement) forces a real trade-off. Minor deduction: with round-robin the
chair may speak before compliance has argued, and the termination check's
dependence on exact wording is fragile with small local models.

### 15 — Magentic Business Continuity Drill — 8/10

A smart inversion: the *manager* holds the playbook tool
(`list_playbook_steps`) so its plan is grounded before it delegates — a subtle,
valuable lesson that grounding belongs at the planning layer too. The
FACILITY-DC-EAST fixture (tier-1, drill 410 days overdue against a 365-day
policy) gives specialists real facts to retrieve. Six agents with distinct tool
grants keeps delegation legible. Deduction mirrors 10: the five specialist
workstreams are fairly separable, so replanning pressure is lower than in 05.

## Quote-to-Cash Family (16a–16e)

The *concept* of this family is instructor gold: hold the business story, the
six roles, and the `quote-to-cash-context` MCP server constant, and vary only
the orchestration pattern. The fixture design is excellent — the sample request
implies SKUs where one is unavailable (`SKU-TRAINING-1`) and pairs exist that
are incompatible (`SKU-ROUTE-OPT` + `SKU-ANALYTICS-EDGE`), and enterprise terms
carry approval triggers — so differences between patterns show up in *outcomes*,
not just transcripts. Execution across the five variants is uneven, mostly
because four of them reuse `staged_agents()` unchanged rather than adapting
roles to the pattern.

### 16a — Sequential — 9/10

The anchor of the family and the closest to how quote-to-cash actually runs:
trigger → customer context → SKU discovery → fit validation → pricing/legal →
package. Each stage's single-tool grant makes the stage boundaries crisp, and
downstream stages genuinely consume upstream output (fit validation needs
discovered SKUs; pricing needs validated SKUs). Comparing every other variant
against this one is the family's whole pedagogical payoff.

### 16b — Concurrent — 6/10

Runs the same six *staged* agents in parallel — but the stages are dependent.
`ProductFitAgent` must validate SKUs it never received, and `PricingTermsAgent`
prices SKUs nobody discovered, so both must guess SKUs from the request text;
meanwhile `QuoteGenerationAgent`, holding all seven tools, quietly completes
the entire flow alone in its parallel lane. Experienced instructors can use
this as a deliberate *anti-example* — "watch what happens when you parallelize
a dependent pipeline" — but the learning goal frames the dimensions as
"independent," which they are not. Either reframe the goal as a pattern-fit
lesson or give the parallel agents genuinely independent enrichment briefs.

### 16c — Handoff — 5/10

The weakest scenario in the repository, because the graph structurally cannot
deliver the learning goal. The goal promises routing "to product, pricing,
legal, and quote-generation specialists based on what the request actually
needs," and the `when_to_use` says "the model should choose the route" — but
the wired graph is triage (`QuoteTriggerAgent`, whose instructions say to check
readiness, not to route) → keyword router → **exactly one** specialist → done.
Unless the router's generated keywords happen to land on
`QuoteGenerationAgent`, no quote package is ever produced from a request that
asks for one. Multi-hop handoff, or triage instructions and curated routes
aimed at the quote generator, would make this teachable.

### 16d — Group Chat — 6/10

The premise (debate product fit, pricing risk, legal terms, readiness) is
sound, but the six reused agents are stage *workers*, not reviewers — their
instructions say "validate," "resolve," "assemble," not "argue" or "critique,"
so the transcript reads as six sequential status reports delivered round-robin.
The borrowed termination phrase ("approved" + "recommendation") has no champion
here, so runs typically exhaust 7 messages, and with six participants the
rotation never even completes a second round. Rewriting the instructions into
reviewer stances (as scenarios 04/09/14 do) would lift this substantially.

### 16e — Magentic — 8/10

A strong closer. `manager_first_agents()` promotes `QuoteGenerationAgent` — the
role that owns the deliverable and holds all seven tools — to manager, which is
the right choice: the manager can recognize what's missing, delegate to the
single-tool specialists, and fill gaps itself. Delegation, replanning, and the
ledger limits are all in play, and contrasting this transcript with 16a's fixed
pipeline is the family's best A/B comparison. Deduction: a manager that can do
every subtask with its own tools sometimes just… does them, deflating the
delegation lesson; trimming the manager's tool list to `quote_format_package`
plus the CRM reads would force visible delegation.

---

## Cross-Cutting Recommendations

1. **Rename or rebuild the handoff mechanism.** All four handoff scenarios
   (03, 08, 13, 16c) route via keyword scoring in `HandoffRouterExecutor`, with
   keywords auto-generated from agent names/descriptions. Either curate
   per-route keywords and describe the pattern as "code-defined routing," or
   demonstrate the framework's function-call handoff so the docs' "look for
   function-call handoffs" guidance is true.
2. **Give each group chat its own termination condition.** `stop_after_council`
   is only meaningful for scenario 14; scenarios 04, 09, and 16d effectively
   run on the message cap, and their synthesizer agents rarely speak last.
   A per-scenario terminator (or ordering the synthesizer to close each round)
   would fix both.
3. **Fix scenario 12's summary agent.** An agent instructed to combine peer
   outputs must run after fan-in, not beside it.
4. **Reframe 16b and 16c honestly.** Either adapt the reused staged agents to
   the pattern (independent enrichment briefs for concurrent; a routing-charter
   triage for handoff) or explicitly teach them as pattern-mismatch
   counterexamples — which would itself be valuable instruction.
