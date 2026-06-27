# Learning Path

This repository is designed to teach two separate choices that often get mixed together:

- API boundary: Responses API or Invocations API.
- Orchestration pattern: sequential, concurrent, handoff, group chat, or magentic.

## Recommended Order

1. Start with `responses-api-release-room/notebooks/01-sequential-release-readiness.ipynb`.
   Learn the simplest path: one Responses request enters a fixed multi-agent pipeline.
2. Run `invocations-api-review-bot/notebooks/01-sequential-release-readiness.ipynb`.
   Compare how the same pattern changes when the input is a custom job payload.
3. Continue through scenarios `02` to `05` in both directories.
   Keep the scenario number the same when comparing APIs so only the API boundary changes.
4. Run scenarios `06` to `10` to see the same five patterns inside enterprise application workflows.
   These examples cover HR onboarding, vendor risk, customer entitlement routing, quarterly planning, and supply chain disruption response.
5. Use the HTTP commands in each notebook only after the in-process workflow run is clear.

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
| Concurrent | Independent expert review. | Multiple outputs from parallel specialists. |
| Handoff | Dynamic routing to specialists. | Function-call handoffs and specialist responses. |
| Group chat | Visible critique and refinement. | A transcript-like discussion. |
| Magentic | Manager-led planning and replanning. | Dynamic delegation and investigation. |

## Local Runtime Notes

- The notebooks call Ollama by default, so `ollama serve` must be running and `qwen3:14b` must be pulled.
- Each notebook renders a Mermaid flow diagram through `mermaid.ink`; if remote image rendering is unavailable, inspect the `flow_diagram.mermaid` source returned by the diagram cell.
- `max_tokens` defaults to `500` per agent turn to keep local multi-agent runs practical.
- Group chat and magentic scenarios usually take longer than sequential, concurrent, and handoff scenarios.
- Notebook outputs are intentionally not committed. Re-run cells locally when you want fresh output.
