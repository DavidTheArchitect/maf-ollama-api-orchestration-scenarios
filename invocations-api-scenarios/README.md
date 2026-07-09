# Invocations API Scenarios

This sample hosts 22 Microsoft Agent Framework multi-agent scenarios behind the custom Invocations API.

Use this shape when the caller is not a normal chat client: CI jobs, webhooks, schedulers, internal services, batch processors, or APIs that need a custom payload and response contract.

## How Scenario Selection Works

The request body is owned by this application. Choose the scenario per request:

```json
{
  "scenario": "concurrent-pr-review",
  "task": "Review this PR before merge.",
  "subject": "contoso/orders-api",
  "artifacts": ["src/orders/reconciliation.py"],
  "constraints": ["Return actionable findings."],
  "stream": false
}
```

Supported scenarios:

| Scenario | Pattern | Agents | Learning focus |
| --- | --- | ---: | --- |
| `sequential-release-readiness` | Sequential | 5 | A structured job moves through fixed review stages. |
| `concurrent-pr-review` | Concurrent | 5 | A CI-style payload fans out to independent reviewers. |
| `handoff-support-triage` | Handoff | 5 | A ticket payload routes to the right specialist. |
| `group-chat-launch-council` | Group chat | 5 | A change advisory record is produced from a stakeholder discussion. |
| `magentic-incident-response` | Magentic | 6 | A manager-led incident workflow dynamically coordinates specialists. |
| `sequential-employee-onboarding` | Sequential | 5 | A structured onboarding job moves through required enterprise departments. |
| `concurrent-vendor-risk-assessment` | Concurrent | 5 | A vendor intake payload fans out to independent enterprise risk reviewers. |
| `handoff-customer-entitlement` | Handoff | 5 | A customer entitlement case routes to the right enterprise specialist. |
| `group-chat-quarterly-planning` | Group chat | 5 | A stakeholder planning job returns a decision record from a council discussion. |
| `magentic-supply-chain-disruption` | Magentic | 6 | A manager-led operations job coordinates dynamic disruption response planning. |
| `sequential-procurement-approval` | Sequential + MCP | 5 | A grounded procurement approval pipeline uses local enterprise-context tools. |
| `concurrent-security-alert-enrichment` | Concurrent + MCP | 5 | Independent alert-enrichment lanes fan in to an incident summary agent. |
| `handoff-claims-exception-routing` | Handoff + MCP | 5 | A grounded triage decision routes a claim, then customer communications finishes. |
| `group-chat-policy-exception-board` | Group chat + MCP | 4 | A board debates a policy exception using deterministic enterprise context. |
| `magentic-business-continuity-drill` | Magentic + MCP | 6 | A manager-led continuity drill delegates against facility and policy facts. |
| `scenario-16-quote-to-cash-sequential` | Sequential + MCP | 6 | Quote-to-cash runs as a staged CRM, product, pricing, legal, and quote pipeline. |
| `scenario-16-quote-to-cash-concurrent` | Concurrent + MCP | 6 | Quote lanes enrich the same request independently, then a quote owner reconciles them. |
| `scenario-16-quote-to-cash-handoff` | Handoff + MCP | 6 | A trigger routes to the most-needed quote specialist; the quote owner always finishes. |
| `scenario-16-quote-to-cash-group-chat` | Group chat + MCP | 6 | Quote reviewers debate readiness, SKU fit, and pricing risk before a verdict. |
| `scenario-16-quote-to-cash-magentic` | Magentic + MCP | 6 | A quote manager dynamically delegates until the quote package is ready. |
| `group-chat-partner-launch-review` | Group chat + A2A | 5 | Two seats are remote partner agents reached through Agent2Agent. |
| `scenario-18-agent-framework-primitives` | Sequential + primitives lab | 5 | A capstone notebook maps common Agent Framework primitives with one concept per cell. |

Each scenario definition lives in its own module under `src/invocations_scenarios/scenarios/`. The `notebooks/` directory contains one companion notebook per scenario with executable learning cells.
Each notebook includes a Mermaid flow diagram cell that renders through `mermaid.ink` at runtime and returns the Mermaid source for inspection or copy/paste.

Scenarios 11-15 use a bundled deterministic `enterprise-context` MCP stdio server. Scenario 16 uses a separate `quote-to-cash-context` MCP server across all five orchestration patterns. Scenario 17 starts a local A2A partner-agent server in-process for notebooks and sample runs. Scenario 18 is a primitive lab covering the common local Agent Framework building blocks and explicitly naming cloud-hosted primitives that are excluded from this Ollama workspace.

## API And Pattern Comparison

| Pattern | API boundary | Scenario choice | Best learning use |
| --- | --- | --- | --- |
| Sequential | `/invocations` | Per request | Run a structured job through required stages. |
| Concurrent | `/invocations` | Per request | Fan out a CI or webhook payload to independent reviewers. |
| Handoff | `/invocations` | Per request | Route a ticket or job to the right specialist. |
| Group chat | `/invocations` | Per request | Return a decision record from a stakeholder-style discussion. |
| Magentic | `/invocations` | Per request | Coordinate dynamic incident-style work from a custom payload. |

## Install

```powershell
ollama pull gemma4:12b
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
```

## Run And Invoke

```powershell
python -m invocations_scenarios --model gemma4:12b --port 8089
```

Invoke a scenario:

```powershell
(Invoke-WebRequest -Uri http://localhost:8089/invocations -Method POST -ContentType "application/json" -Body (Get-Content .\samples\concurrent-pr-review.json -Raw)).Content
```

Multi-turn with explicit session:

```powershell
(Invoke-WebRequest -Uri "http://localhost:8089/invocations?agent_session_id=demo-session" -Method POST -ContentType "application/json" -Body (Get-Content .\samples\handoff-support-triage.json -Raw)).Content
```

Streaming:

```powershell
Invoke-WebRequest -Uri http://localhost:8089/invocations -Method POST -ContentType "application/json" -Body (Get-Content .\samples\magentic-incident-response-streaming.json -Raw)
```

## When Invocations API Fits

- The caller is a webhook, CI system, scheduler, or internal service.
- The input is not naturally an OpenAI Responses payload.
- You need custom fields such as `scenario`, `subject`, `artifacts`, or domain-specific options.
- You want a custom JSON response with application metadata.
- You want to define your own streaming protocol.

## Backward Compatibility

- `pattern` is accepted as an alias when `scenario` is omitted, mapping to the default scenario for that pattern.
- Old `repo` maps to `subject`.
- Old `changed_files` maps to `artifacts`.

## Local Session Warning

This sample stores session summaries in memory. That is useful for local learning, but it is lost when the process restarts. Use durable storage for production.

## Ollama Notes

- This sample uses the native `agent-framework-ollama` provider, so model calls stay local.
- Use `--ollama-host`, `--temperature`, `--num-ctx`, `--max-tokens`, `--keep-alive`, and `--think` to tune the local Ollama runtime.
- `--max-tokens` is optional. Without it, each request scenario uses its own `1000` or `1500` token budget per agent turn.
- Notebook outputs are intentionally not committed. Run a notebook from this project virtual environment after installing with `python -m pip install -e . --no-deps`.
- Ollama supports local function tools through Agent Framework, but it does not provide hosted tools such as hosted code interpreter, file search, web search, or hosted MCP.
