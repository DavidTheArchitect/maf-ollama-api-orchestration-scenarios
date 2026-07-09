# Learning Path

This repository is designed to teach two separate choices that often get mixed together:

- API boundary: Responses API or Invocations API.
- Orchestration pattern: sequential, concurrent, handoff, group chat, or magentic.

## Recommended Order

1. Start with `responses-api-scenarios/notebooks/01-sequential-release-readiness.ipynb`.
   Learn the simplest path: one Responses request enters a fixed multi-agent pipeline.
2. Run `invocations-api-scenarios/notebooks/01-sequential-release-readiness.ipynb`.
   Compare how the same pattern changes when the input is a custom job payload.
3. Continue through scenarios `02` to `05` in both directories.
   Keep the scenario number the same when comparing APIs so only the API boundary changes.
4. Run scenarios `06` to `10` to see the same five patterns inside enterprise application workflows.
   These examples cover HR onboarding, vendor risk, customer entitlement routing, quarterly planning, and supply chain disruption response.
5. Run scenarios `11` to `15` to learn MCP tool usage, one scenario per orchestration pattern.
   These attach a local `enterprise-context` MCP server (no network, credentials, or setup) and cover procurement approval, security alert enrichment, claims exception routing, a policy exception board, and a business continuity drill. Each MCP notebook adds an MCP tool context section and dashed tool links in the flow diagram.
6. Run the Scenario 16 quote-to-cash family (`16a` to `16e`) to compare all five patterns over one shared business story.
   These reuse the same six instruction-led LLM agent roles (trigger, customer context, SKU discovery, product fit, pricing/terms, quote generation) grounded by a local `quote-to-cash-context` MCP server, so you can compare how the same business process changes under each orchestration pattern.
7. Run scenario 17 (`17-group-chat-partner-launch-review`) to learn the A2A protocol: two council seats
   are remote partner agents behind agent cards and JSON-RPC endpoints, hosted by a bundled deterministic
   A2A server the notebook starts in-process. Compare it with the MCP scenarios: MCP grounded agents in
   tools; A2A seats peer agents from other organizations, with the group-chat orchestration unchanged.
8. Run scenario 18 (`18-agent-framework-primitives-lab`) as a capstone map of the framework primitives.
   Each cell teaches one building block: messages, agents, tools, MCP, A2A, workflow executors, graph
   builders, orchestration builders, hosting, and observability.
9. Use the HTTP commands in each notebook only after the in-process workflow run is clear.

## Responses API vs Invocations API

| Question | Responses API | Invocations API |
| --- | --- | --- |
| What does the client send? | OpenAI-compatible `input` and `stream` fields. | Application-owned JSON such as `scenario`, `task`, `subject`, and `artifacts`. |
| Where is the scenario chosen? | At server startup with `--scenario`. | Per request in the JSON payload. |
| What client fits best? | Chat UI, OpenAI-compatible SDK, conversational app. | Webhook, CI job, scheduler, internal service, batch job. |
| What does streaming look like? | Responses API event stream. | App-defined event stream. |
| Who owns the response shape? | The Responses protocol. | The application handler. |

## Orchestration Pattern Guide

| Pattern | Learn it when you need | Look for |
| --- | --- | --- |
| Sequential | A fixed pipeline with required stages. | Each agent transforms prior output. |
| Concurrent | Independent expert review. | Labelled outputs from parallel specialists; scenarios with a synthesizer run it after fan-in to combine them. |
| Handoff | Dynamic routing to specialists. | A triage `ROUTE:` directive validated by a code-defined router, plus the routed specialist (and optional finisher) responses. |
| Group chat | Visible critique and refinement. | A cycle-based discussion whose closing agent ends a converged round with an explicit verdict line. |
| Magentic | Manager-led planning and replanning. | Dynamic delegation and investigation. |

## Notebook Layout

Every notebook is laid out cell-per-concept: fixtures are separate from tool functions
(the tool cell ends with a direct grounded call), workflow plumbing is separate from the
pattern's own machinery, and every pattern cell ends with an offline demo -- a router
choosing a route, a termination function firing at a cycle boundary -- that runs without
Ollama. Each scenario's "What to Inspect" and "Experiments" sections point at that
scenario's engineered wrinkle (an expired review, a conflicting policy, a discount over
the legal threshold), so learners know what a correct run should surface.

## Manual Live-Run Verification

When validating changes with a local Ollama (`gemma4:12b` pulled), run one notebook per
pattern tier end-to-end and check the scenario spotlight is surfaced:

1. `01-sequential-release-readiness` -- the brief cites the finance freeze and rollback constraint.
2. `07-concurrent-vendor-risk-assessment` -- finance engages the 150k budget cap.
3. `13-handoff-claims-exception-routing` -- the ROUTE line picks fraud first; comms finishes.
4. `14-group-chat-policy-exception-board` -- the chair's expiry honors the 60-day cap.
5. `16e-scenario-16-quote-to-cash-magentic` -- the manager delegates pricing/legal for the 25% discount.

## Local Runtime Notes

- The notebooks call Ollama by default, so `ollama serve` must be running and `gemma4:12b` must be pulled.
- Each notebook renders a Mermaid flow diagram through `mermaid.ink`; if remote image rendering is unavailable, inspect the `flow_diagram.mermaid` source returned by the diagram cell.
- `max_tokens` defaults per scenario: `1000` for lighter flows and `1500` for heavier group-chat, magentic, quote-to-cash, A2A, and primitives-lab flows.
- Group chat and magentic scenarios usually take longer than sequential, concurrent, and handoff scenarios.
- Notebook outputs are intentionally not committed. Re-run cells locally when you want fresh output.
