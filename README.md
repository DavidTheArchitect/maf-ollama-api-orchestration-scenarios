# Microsoft Agent Framework: Responses API vs Invocations API

This workspace contains two local Python learning samples that use Microsoft Agent Framework (MAF) multi-agent orchestration with Ollama as the local model provider.

The goal is to compare the API boundary while keeping the orchestration patterns parallel:

Repository URL: https://github.com/DavidTheArchitect/maf-ollama-api-orchestration-scenarios

Start with [LEARNING_PATH.md](LEARNING_PATH.md) if your goal is to compare when to use Responses API, Invocations API, and each orchestration pattern.

| Directory | Hosted API | Scenario selection | Best for | Patterns shown |
| --- | --- | --- | --- | --- |
| `responses-api-scenarios/` | OpenAI-compatible Responses API | Server startup via `--scenario` | Conversational apps, streaming chat clients, OpenAI-compatible tooling, multi-turn chat state | Sequential, concurrent, handoff, group chat, magentic |
| `invocations-api-scenarios/` | Custom Invocations API | Per request via `scenario` | Webhooks, structured jobs, non-chat payloads, custom response contracts | Sequential, concurrent, handoff, group chat, magentic |

## Scenario Catalog

Both directories now contain the same twenty-two learning scenarios so the API differences are easy to compare. The first five focus on software delivery/support workflows; the next five focus on enterprise application workflows; scenarios 11-15 teach MCP tool usage; the Scenario 16 quote-to-cash family teaches one shared business story across all five patterns; Scenario 17 teaches the A2A protocol by seating remote partner agents in a group chat; and Scenario 18 teaches the common Microsoft Agent Framework primitives in one lab:

| Scenario | Pattern | Core lesson |
| --- | --- | --- |
| `sequential-release-readiness` | Sequential | Fixed agent pipeline where each stage transforms the previous output. |
| `concurrent-pr-review` | Concurrent | Parallel specialist review with aggregated output. |
| `handoff-support-triage` | Handoff | Dynamic routing between specialists based on context. |
| `group-chat-launch-council` | Group chat | Iterative multi-agent discussion and critique. |
| `magentic-incident-response` | Magentic | Manager-led dynamic planning and coordination. |
| `sequential-employee-onboarding` | Sequential | Enterprise onboarding pipeline across HR, IT, security, payroll, and enablement. |
| `concurrent-vendor-risk-assessment` | Concurrent | Parallel vendor review across security, privacy, legal, finance, and operations. |
| `handoff-customer-entitlement` | Handoff | Customer entitlement case routing across billing, contract, support, and engineering. |
| `group-chat-quarterly-planning` | Group chat | Cross-functional business planning discussion with stakeholder tradeoffs. |
| `magentic-supply-chain-disruption` | Magentic | Manager-led response to a supply chain disruption across enterprise functions. |
| `sequential-procurement-approval` | Sequential | MCP-grounded approval pipeline across intake, budget, security, legal, and packaging. |
| `concurrent-security-alert-enrichment` | Concurrent | Independent identity, endpoint, network, and data-loss enrichment of one alert via MCP tools, combined by a summary agent after fan-in. |
| `handoff-claims-exception-routing` | Handoff | Triage names the claim's owner with a ROUTE directive grounded in MCP facts; customer comms always finishes the run. |
| `group-chat-policy-exception-board` | Group chat | Board debates a policy exception with MCP-grounded risk, business need, and compliance. |
| `magentic-business-continuity-drill` | Magentic | Manager plans and delegates a continuity drill across facilities, IT, comms, finance, and operations. |
| `scenario-16-quote-to-cash-sequential` | Sequential | Quote-to-cash as a staged pipeline: CRM context, product context, pricing/legal, quote package. |
| `scenario-16-quote-to-cash-concurrent` | Concurrent | Self-sufficient parallel lanes enrich the quote; the quote owner reconciles them after fan-in. |
| `scenario-16-quote-to-cash-handoff` | Handoff | The trigger names the specialist the quote needs most via a ROUTE directive; the quote owner always finishes the package. |
| `scenario-16-quote-to-cash-group-chat` | Group chat | Reviewers debate readiness, fit, SKUs, and pricing risk; the quote owner closes each round with a verdict. |
| `scenario-16-quote-to-cash-magentic` | Magentic | Manager-led planning that delegates and replans until the quote package is ready. |
| `group-chat-partner-launch-review` | Group chat + A2A | Two council seats are remote partner agents reached over the A2A protocol; the orchestration is unchanged. |
| `scenario-18-agent-framework-primitives` | Sequential + primitives lab | One notebook maps the common Agent Framework primitives: messages, agents, tools, MCP, A2A, workflow executors, builders, hosting, and observability. |

Scenarios 11-15 attach a local, deterministic `enterprise-context` MCP server (FastMCP over stdio) exposing `lookup_enterprise_record`, `search_policy`, `calculate_priority_score`, `list_playbook_steps`, and `create_decision_log_entry`.

The **Scenario 16 quote-to-cash** family (`16a`-`16e`) uses one quote request to compare how instruction-led LLM agents behave under each orchestration pattern. All five variants reuse the same six roles — `QuoteTriggerAgent`, `CustomerContextAgent`, `SkuDiscoveryAgent`, `ProductFitAgent`, `PricingTermsAgent`, `QuoteGenerationAgent` — grounded by a second local MCP server, `quote-to-cash-context`, exposing `crm_get_quote_trigger`, `crm_get_customer_profile`, `product_search_catalog`, `product_validate_skus`, `pricing_calculate_quote`, `legal_evaluate_terms`, and `quote_format_package`. Every scenario module (01-17) supports `python -m <package>.scenarios.<module>` for a direct run, via a shared `scenarios/_runner.py` helper.

**Scenario 17** (`group-chat-partner-launch-review`) adds the protocol counterpart to MCP: where MCP connects an agent to *tools*, **A2A (Agent2Agent)** connects an agent to *peer agents* owned by other organizations. A bundled `partner-agents` A2A server (deterministic by default, `--ollama` optional) hosts the two partner seats behind real agent cards and JSON-RPC endpoints; the group-chat orchestration is reused unchanged. Start it with `python -m <package>.a2a_servers.partner_agents --port 8765`, or let the notebook and `run_sample()` start it in-process on an ephemeral port.

**Scenario 18** (`scenario-18-agent-framework-primitives`) is a high-level primitives lab. Its notebook uses a sequential runtime shell so it still runs through the existing sample servers, but the notebook itself is a cell-per-primitive walkthrough covering the practical local set: `Message`, chat-client-backed agents, function tools, session/thread state, streaming, `MCPStdioTool`, `A2AAgent`, `Executor`, `@handler`, `WorkflowContext`, `AgentExecutor`, `WorkflowBuilder`, fan-out/fan-in, handoff routing, `GroupChatBuilder`, `MagenticBuilder`, hosting, and observability. Hosted file search, hosted code interpreter, web search, Foundry toolboxes, durable persistence, and cloud memory providers are named as exclusions because they do not fit this local Ollama workspace.

Both MCP servers need no network, credentials, or manual setup. Agents with declared `mcp_tools` receive a tool via Agent Framework `MCPStdioTool` (`approval_mode="never_require"`, per-agent `allowed_tools`); the server modules live under `src/.../mcp_servers/` in each package and the agent's `mcp_server` field selects which one to attach.

Each scenario is defined in its own Python module inside the API directory's `src/.../scenarios/` package. Each API directory also has a `notebooks/` folder with one companion notebook per scenario, laid out cell-per-concept: fixtures, tool functions, agent roster, workflow plumbing, and the pattern's own machinery each get a runnable cell with visible output, and every pattern cell ends with an offline demo that runs without Ollama. MCP scenario notebooks add an MCP tool context section and dashed tool links in the flow diagram.
Each notebook includes a runtime Mermaid flow diagram that renders through `mermaid.ink` and also exposes the generated Mermaid source.

## Instruction-Led Agents And Orchestration

Every agent is an **LLM-backed agent with role instructions**. Most starter scenarios use instructions only, so the orchestration pattern is easy to see. Enterprise and quote-to-cash scenarios add domain tools when the lesson needs grounded context.

- **Instruction-led agents**: each role is created with `OllamaChatClient(...).as_agent(...)`, a name, a description, and instructions. Optional MCP/domain tools are attached only when the scenario teaches tool-grounded behavior.
- **Code-defined orchestration** (`src/.../executors.py`, `workflows.py`): Sequential, Concurrent, and Handoff are built as explicit `WorkflowBuilder` graphs of custom `Executor` subclasses with agent nodes wrapped in `AgentExecutor`. They use typed `@handler` methods, shared `WorkflowContext` state, conditional routing, and fan-out/fan-in — for example `PromptDispatchExecutor`, `StageGateExecutor`, `ConcurrentAggregatorExecutor`, and `HandoffRouterExecutor`. Group Chat and Magentic use the framework's code-driven builders (custom selection function, manager planning, ledger limits).

The point of the repo is to show how ordinary instruction-led LLM agents become more capable together when the framework coordinates the turn order, routing, aggregation, group discussion, or manager-led delegation. The custom-executor graphs are validated offline with a deterministic stub agent, so the wiring is exercised without a model; live runs use Ollama. Notebooks render in the **Aptos** font (with a graceful fallback) and include an agent capability map.

## Learning Artifacts

| Artifact | Purpose |
| --- | --- |
| `LEARNING_PATH.md` | Recommended study order and API/pattern decision guide. |
| `responses-api-scenarios/notebooks/` | One notebook per Responses scenario, using in-process workflow execution by default. |
| `invocations-api-scenarios/notebooks/` | One notebook per Invocations scenario, using the custom payload and response contract. |
| `src/.../scenarios/*.py` | One Python module per scenario so learners can inspect scenario definitions directly. |

## Prerequisites

- Python 3.11 or later. This machine has Python 3.13.5.
- Ollama installed and running locally.
- GitHub CLI and Git if you want to clone or contribute to the repository.
- Recommended local model:

```powershell
ollama pull gemma4:12b
ollama run gemma4:12b "Return only OK"
```

Each sample has its own `requirements.txt`. The Agent Framework packages are still preview, so install with `--pre`.

## Responses API Quick Start

```powershell
cd responses-api-scenarios
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python -m responses_scenarios --scenario sequential-release-readiness --model gemma4:12b --port 8088
```

In a second terminal:

```powershell
(Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\sequential-release-readiness.json -Raw)).Content
```

## Invocations API Quick Start

```powershell
cd invocations-api-scenarios
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python -m invocations_scenarios --model gemma4:12b --port 8089
```

In a second terminal:

```powershell
(Invoke-WebRequest -Uri http://localhost:8089/invocations -Method POST -ContentType "application/json" -Body (Get-Content .\samples\concurrent-pr-review.json -Raw)).Content
```

## What To Compare

- Request body shape: Responses keeps the OpenAI Responses shape; Invocations owns the whole JSON contract.
- Scenario choice: Responses chooses a scenario when the server starts; Invocations chooses a scenario in each request.
- Client compatibility: Responses can be called by OpenAI-compatible clients; Invocations is better when your app already has a custom payload.
- State: Responses is designed around conversation/session lifecycle; Invocations can still support sessions, but the handler decides how.
- Streaming: Responses emits Responses API events; Invocations can stream any protocol you choose.
- Model provider: both samples use the native `agent-framework-ollama` provider. This keeps model access local.

## Local Verification

Run these checks from the repository root after installing dependencies:

```powershell
python -m compileall responses-api-scenarios invocations-api-scenarios
cd responses-api-scenarios
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..\invocations-api-scenarios
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..
$files = rg --files -g "*.json" -g "!**/.venv/**"
foreach ($file in $files) { $null = Get-Content $file -Raw | ConvertFrom-Json; $file }
```

Live scenario runs require Ollama to be running with `gemma4:12b` or your selected `OLLAMA_MODEL` already pulled. Scenarios default to either `1000` or `1500` max tokens per agent turn: lighter deterministic flows use `1000`, while group-chat, magentic, quote-to-cash, A2A, and primitives-lab flows use `1500`. Set `OLLAMA_MAX_TOKENS` or pass `--max-tokens` only when you want to override the scenario recommendation.

## References

- Microsoft Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/overview/
- Ollama provider: https://learn.microsoft.com/en-us/agent-framework/agents/providers/ollama
- Ollama Gemma 4 model library: https://ollama.com/library/gemma4
- Foundry Responses and Invocations hosting: https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent
- OpenAI-compatible endpoints: https://learn.microsoft.com/en-us/agent-framework/integrations/openai-endpoints
- Workflow orchestrations: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
