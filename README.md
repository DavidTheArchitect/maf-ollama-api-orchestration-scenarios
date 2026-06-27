# Microsoft Agent Framework: Responses API vs Invocations API

This workspace contains two local Python learning samples that use Microsoft Agent Framework (MAF) multi-agent orchestration with Ollama as the local model provider.

The goal is to compare the API boundary while keeping the orchestration patterns parallel:

Repository URL: https://github.com/DavidTheArchitect/maf-ollama-api-orchestration-scenarios

Start with [LEARNING_PATH.md](LEARNING_PATH.md) if your goal is to compare when to use Responses API, Invocations API, and each orchestration pattern.

| Directory | Hosted API | Scenario selection | Best for | Patterns shown |
| --- | --- | --- | --- | --- |
| `responses-api-release-room/` | OpenAI-compatible Responses API | Server startup via `--scenario` | Conversational apps, streaming chat clients, OpenAI-compatible tooling, multi-turn chat state | Sequential, concurrent, handoff, group chat, magentic |
| `invocations-api-review-bot/` | Custom Invocations API | Per request via `scenario` | Webhooks, structured jobs, non-chat payloads, custom response contracts | Sequential, concurrent, handoff, group chat, magentic |

## Scenario Catalog

Both directories now contain the same five learning scenarios so the API differences are easy to compare:

| Scenario | Pattern | Core lesson |
| --- | --- | --- |
| `sequential-release-readiness` | Sequential | Fixed agent pipeline where each stage transforms the previous output. |
| `concurrent-pr-review` | Concurrent | Parallel specialist review with aggregated output. |
| `handoff-support-triage` | Handoff | Dynamic routing between specialists based on context. |
| `group-chat-launch-council` | Group chat | Iterative multi-agent discussion and critique. |
| `magentic-incident-response` | Magentic | Manager-led dynamic planning and coordination. |

Each scenario is now defined in its own Python module inside the API directory's `src/.../scenarios/` package. Each API directory also has a `notebooks/` folder with one companion notebook per scenario for step-by-step learning and live in-process Ollama execution.

## Learning Artifacts

| Artifact | Purpose |
| --- | --- |
| `LEARNING_PATH.md` | Recommended study order and API/pattern decision guide. |
| `responses-api-release-room/notebooks/` | One notebook per Responses scenario, using in-process workflow execution by default. |
| `invocations-api-review-bot/notebooks/` | One notebook per Invocations scenario, using the custom payload and response contract. |
| `src/.../scenarios/*.py` | One Python module per scenario so learners can inspect scenario definitions directly. |

## Prerequisites

- Python 3.11 or later. This machine has Python 3.13.5.
- Ollama installed and running locally.
- GitHub CLI and Git if you want to clone or contribute to the repository.
- Recommended local model:

```powershell
ollama pull qwen3:14b
ollama run qwen3:14b "Return only OK"
```

Each sample has its own `requirements.txt`. The Agent Framework packages are still preview, so install with `--pre`.

## Responses API Quick Start

```powershell
cd responses-api-release-room
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python -m release_room --scenario sequential-release-readiness --model qwen3:14b --max-tokens 500 --port 8088
```

In a second terminal:

```powershell
(Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\sequential-release-readiness.json -Raw)).Content
```

## Invocations API Quick Start

```powershell
cd invocations-api-review-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python -m review_bot --model qwen3:14b --max-tokens 500 --port 8089
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
python -m compileall responses-api-release-room invocations-api-review-bot
cd responses-api-release-room
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..\invocations-api-review-bot
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..
$files = rg --files -g "*.json" -g "!**/.venv/**"
foreach ($file in $files) { $null = Get-Content $file -Raw | ConvertFrom-Json; $file }
```

Live scenario runs require Ollama to be running with `qwen3:14b` or your selected `OLLAMA_MODEL` already pulled. Both samples default `OLLAMA_MAX_TOKENS` to `500` per agent turn so multi-agent local runs finish predictably; raise it when you want longer learning output.

## References

- Microsoft Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/overview/
- Ollama provider: https://learn.microsoft.com/en-us/agent-framework/agents/providers/ollama
- Ollama qwen3 model library: https://ollama.com/library/qwen3
- Foundry Responses and Invocations hosting: https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent
- OpenAI-compatible endpoints: https://learn.microsoft.com/en-us/agent-framework/integrations/openai-endpoints
- Workflow orchestrations: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
