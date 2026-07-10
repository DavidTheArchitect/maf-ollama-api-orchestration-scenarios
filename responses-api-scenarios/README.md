# Responses API Scenarios

This sample hosts 27 Microsoft Agent Framework multi-agent scenarios behind the OpenAI-compatible Responses API.

Use this shape when the caller is a chat UI, OpenAI-compatible SDK, DevUI-style frontend, or anything that benefits from standard `/responses` semantics.

## How Scenario Selection Works

The request body stays Responses-compatible. Choose the scenario when starting the server:

```powershell
python -m responses_scenarios --scenario sequential-release-readiness --port 8088
```

Supported scenarios:

| Scenario | Pattern | Agents | Learning focus |
| --- | --- | ---: | --- |
| `sequential-release-readiness` | Sequential | 5 | A fixed release-readiness pipeline where each agent transforms the prior output. |
| `concurrent-pr-review` | Concurrent | 5 | One chat request fans out to independent specialist reviewers. |
| `handoff-support-triage` | Handoff | 5 | A triage agent routes a conversational issue to the right specialist. |
| `group-chat-launch-council` | Group chat | 5 | A visible council iteratively critiques and refines a launch decision. |
| `magentic-incident-response` | Magentic | 6 | A manager agent dynamically coordinates specialists for open-ended incident work. |
| `sequential-employee-onboarding` | Sequential | 5 | An enterprise onboarding request moves through HR, IT, security, payroll, and enablement stages. |
| `concurrent-vendor-risk-assessment` | Concurrent | 5 | A vendor approval request fans out to independent enterprise risk reviewers. |
| `handoff-customer-entitlement` | Handoff | 5 | A customer entitlement issue routes to billing, contract, support, or engineering specialists. |
| `group-chat-quarterly-planning` | Group chat | 5 | A cross-functional planning council debates retention, roadmap, support, revenue, and margin tradeoffs. |
| `magentic-supply-chain-disruption` | Magentic | 6 | A manager agent coordinates dynamic response planning for a supply chain disruption. |
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
| `sequential-loan-origination` | Sequential + MCP | 5 | A regulated underwriting pipeline walks fixed intake, credit, income, pricing, and offer stages. |
| `concurrent-ma-due-diligence` | Concurrent + MCP | 5 | Independent finance, legal, technology, and market lanes fan in to a deal-lead synthesizer. |
| `handoff-transaction-dispute` | Handoff + MCP | 5 | Triage routes a disputed charge by its dominant signal; customer comms always finishes. |
| `group-chat-architecture-review` | Group chat + MCP | 5 | A build-versus-buy board debates cost, security, residency, and delivery before the chair decides. |
| `magentic-churn-spike-investigation` | Magentic + MCP | 6 | A manager plans, delegates, and replans an ambiguous churn root-cause investigation. |

Each scenario definition lives in its own module under `src/responses_scenarios/scenarios/`. The `notebooks/` directory contains one companion notebook per scenario with executable learning cells.
Each notebook includes a Mermaid flow diagram cell that renders through `mermaid.ink` at runtime and returns the Mermaid source for inspection or copy/paste.

Scenarios 11-15 use a bundled deterministic `enterprise-context` MCP stdio server. Scenario 16 uses a separate `quote-to-cash-context` MCP server across all five orchestration patterns. Scenario 17 starts a local A2A partner-agent server in-process for notebooks and sample runs. Scenario 18 is a primitive lab covering the common local Agent Framework building blocks and explicitly naming cloud-hosted primitives that are excluded from this Ollama workspace.

## API And Pattern Comparison

| Pattern | API boundary | Scenario choice | Best learning use |
| --- | --- | --- | --- |
| Sequential | `/responses` | Server startup | Hide a fixed multi-agent pipeline behind a chat-compatible endpoint. |
| Concurrent | `/responses` | Server startup | Fan out one conversational request to independent reviewers. |
| Handoff | `/responses` | Server startup | Let a conversation route itself while the client keeps the same request shape. |
| Group chat | `/responses` | Server startup | Surface collaborative discussion through a standard response stream. |
| Magentic | `/responses` | Server startup | Coordinate open-ended work while preserving a Responses-compatible client contract. |

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

Start one scenario:

```powershell
python -m responses_scenarios --scenario group-chat-launch-council --model gemma4:12b --port 8088
```

Invoke with a normal Responses-style payload:

```powershell
(Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\group-chat-launch-council.json -Raw)).Content
```

Streaming:

```powershell
python -m responses_scenarios --scenario magentic-incident-response --model gemma4:12b --port 8088
Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\magentic-incident-response-streaming.json -Raw)
```

## When Responses API Fits

- You want a standard OpenAI-compatible endpoint.
- Your client is conversational and should not know about internal orchestration details.
- You want to swap orchestration behind a stable `/responses` contract.
- You want standard Responses streaming and conversation behavior.

## Notes

- This sample uses the native `agent-framework-ollama` provider, so model calls stay local.
- Use `--ollama-host`, `--temperature`, `--num-ctx`, `--max-tokens`, `--keep-alive`, and `--think` to tune the local Ollama runtime without changing the API shape.
- `--max-tokens` is optional. Without it, each scenario uses its own `1000` or `1500` token budget per agent turn.
- Notebook outputs are intentionally not committed. Run a notebook from this project virtual environment after installing with `python -m pip install -e . --no-deps`.
- Ollama supports local function tools through Agent Framework, but it does not provide hosted tools such as hosted code interpreter, file search, web search, or hosted MCP.
- `--workflow` still works as a deprecated alias for the old sample and maps pattern names to the matching scenario.
