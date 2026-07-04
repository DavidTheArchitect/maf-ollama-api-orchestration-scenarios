# Plan: Scenario 17 — Group Chat over the A2A Protocol

An instructor's implementation plan for adding a new learning scenario that
combines the **A2A (Agent2Agent) protocol** with the **group chat**
orchestration pattern, following the conventions established by scenarios
01–16 and the improvement pass (PRs #6–#9).

## The Lesson

Every existing scenario coordinates agents that live in the same process.
A2A is the missing counterpart to the repository's MCP lesson:

- **MCP** connects an agent to *tools*.
- **A2A** connects an agent to *other agents* — peers owned by another team,
  company, or runtime, reached over HTTP/JSON-RPC, with their own model,
  tools, and instructions hidden behind an agent card.

Group chat is the ideal pattern to teach A2A because a council seat is
exactly what a remote peer agent looks like: same turn, same transcript,
different owner. The punchline for learners: **the orchestration code does
not change at all** — `GroupChatBuilder`, the round-robin selector, and the
cycle-boundary termination from PR #8 are reused verbatim; only *where two
of the participants live* changes.

## Verified Technical Basis

Confirmed against the installed framework (agent-framework-core 1.10.0):

- `agent-framework-a2a` (preview; install with `--pre`) provides:
  - `A2AAgent` — a client that wraps a remote A2A agent by URL, `AgentCard`,
    or existing A2A `Client`; converts framework Messages to A2A Messages
    and back; inherits `BaseAgent` capabilities.
  - `A2AExecutor` — the server-side bridge that exposes any framework agent
    (`SupportsAgentRun`) over the A2A protocol.
  - `A2AAgentSession` — session/history management for A2A conversations.
- `a2a-sdk` (1.1.0 on PyPI) supplies the hosting machinery (agent card,
  request handlers, Starlette app).

## Scenario Design

**`group-chat-partner-launch-review`** — *"Group Chat Partner Launch Review
(A2A)"*: a joint go-to-market launch council for a co-sold integration,
where two seats belong to outside organizations.

| Seat | Runs | Role |
| --- | --- | --- |
| `ProductLeadAgent` | local Ollama | Argues product readiness and scope |
| `OperationsLeadAgent` | local Ollama | Argues support and operational readiness |
| `PartnerSolutionsAgent` | **remote via A2A** | The ISV partner's agent: argues from partner-side integration status |
| `ExternalComplianceAgent` | **remote via A2A** | An external audit firm's agent: argues certification and compliance status |
| `JointLaunchChairAgent` | local Ollama | Closes each cycle; ends a converged round with `FINAL RECOMMENDATION:` (reusing `termination_phrases`) |

### The partner A2A server

A new `a2a_servers/partner_agents.py` module in each package follows the
bundled-MCP-server philosophy exactly:

- Hosts the two partner agents via `A2AExecutor` plus the `a2a-sdk`
  Starlette app. Localhost only; no credentials; no writes.
- **Deterministic by default**: partner answers are computed from embedded
  fixture data engineered to create a real debate (for example, a partner
  certification that expires mid-launch-window and one failing integration
  test), so tool-free grounding still changes the council's outcome.
- An optional `--ollama` flag serves real LLM-backed partner agents for the
  full agent-to-agent experience.
- A small `PartnerA2AServer` helper starts uvicorn on an ephemeral port in a
  background thread, so notebooks and tests need no second terminal.

### Wiring

- `AgentSpec` gains `a2a_url: str | None = None` (mirroring how
  `mcp_server` selects tool attachment). The agent factory returns
  `A2AAgent(url=...)` for those seats and an Ollama agent otherwise.
- `A2A_PARTNER_BASE_URL` env var (default `http://localhost:8765`) makes the
  partner endpoint configurable.
- `build_group_chat_workflow` is untouched — that is the lesson.

## Work Plan (one PR, same cadence as #6–#9)

1. **Spike (do first).** Verify `A2AAgent` is accepted as a
   `GroupChatBuilder` participant (it inherits `BaseAgent`; the builder's
   docs demand `Agent` — if rejected, wrap it in a thin adapter, decided by
   the spike, not mid-implementation). Confirm a2a-sdk 1.1's agent-card
   endpoint path and uvicorn-in-thread startup, and round-trip one
   deterministic message.
2. **Hosting module.** `a2a_servers/partner_agents.py` in both packages +
   the `PartnerA2AServer` in-process launcher; add `agent-framework-a2a`
   (with `--pre`) and `a2a-sdk>=1.1,<2` to both `requirements.txt`.
3. **Client + scenario.** `AgentSpec.a2a_url`, factory branch, the scenario
   module in both packages (job-payload framing on the invocations side).
4. **Diagrams + notebooks.** The group-chat diagram draws the two remote
   seats inside a "Partner org (A2A)" subgraph with dashed protocol edges
   (visual rhyme with the MCP tool links). The notebook generator gains an
   "A2A Partner Context" cell that inlines the deterministic server the way
   MCP tools are inlined, plus the new scaffold field; notebook `17-…`
   generated for both packages; `test_notebooks` markers extended.
5. **Docs.** README catalog row plus an "MCP vs A2A" comparison note,
   LEARNING_PATH step for running 17 after the MCP scenarios, and a
   SCENARIO_RATINGS entry once the scenario is rated against the rubric
   (target: 9 — novel protocol lesson, unchanged orchestration,
   deterministic grounding).

## Test Plan (all offline, no Ollama)

- **Protocol integration test**: start the deterministic partner server on
  an ephemeral port in-process, create the two `A2AAgent`s, run them
  directly, and assert fixture content round-trips over real JSON-RPC — a
  genuine A2A protocol exercise with zero LLM calls.
- **Unit tests**: the factory returns an `A2AAgent` for A2A seats and an
  Ollama agent otherwise; the scenario declares termination phrases its
  chair is instructed to say (the existing group-chat test picks this up
  automatically); the workflow builds.
- Both suites, `compileall`, and notebook regeneration — the same gate every
  prior PR passed.

## Open Decision

`test_patterns_are_complete_and_balanced` asserts every pattern has the same
number of scenarios (currently 4 x 5). A single group-chat addition breaks
that invariant. Options:

1. **Amend the test** to assert explicit per-pattern counts (group-chat: 5,
   others: 4) with a comment explaining scenario 17 — small, honest, ships
   this plan as scoped. *(Recommended.)*
2. **Build a full Scenario 17 A2A family** (all five patterns over the
   partner story, like Scenario 16) — pedagogically strong but roughly five
   times the scope; better as a follow-up once the group-chat variant proves
   the A2A infrastructure.

## Risks

- `agent-framework-a2a` is a preview package; it only installs with `--pre`
  (consistent with the repository's existing install instructions).
- The `GroupChatBuilder`-participant compatibility of `A2AAgent` is the one
  unverified assumption; the spike resolves it before any scenario code is
  written.
- Live runs keep the remote partner seats deterministic by default, so a
  full live run still needs Ollama only for the three local seats.
