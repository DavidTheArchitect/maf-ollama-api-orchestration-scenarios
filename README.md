# Microsoft Agent Framework: Responses API vs Invocations API

This workspace contains two local Python learning samples that use Microsoft Agent Framework (MAF) multi-agent orchestration with GitHub Copilot as the model provider.

The goal is to compare the API boundary while keeping the orchestration patterns parallel:

Repository URL: https://github.com/DavidTheArchitect/maf-copilot-api-orchestration-scenarios

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

## Prerequisites

- Python 3.11 or later. This machine has Python 3.13.5.
- GitHub Copilot subscription.
- GitHub CLI and Git if you want to clone or contribute to the repository.
- GitHub Copilot SDK runtime:

```powershell
python -m pip install github-copilot-sdk
python -m copilot download-runtime
```

Each sample has its own `requirements.txt`. The Copilot integration package is still preview, so install with `--pre`.

## Responses API Quick Start

```powershell
cd responses-api-release-room
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --pre -r requirements.txt
python -m pip install -e . --no-deps
Copy-Item .env.example .env
python -m release_room --scenario sequential-release-readiness --port 8088
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
python -m review_bot --port 8089
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

## Local Verification

Run these checks from the repository root after installing dependencies:

```powershell
python -m compileall responses-api-release-room invocations-api-review-bot
cd responses-api-release-room
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..\invocations-api-review-bot
$env:PYTHONPATH='src'; $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
cd ..
Get-ChildItem -Recurse -Filter *.json | ForEach-Object { $null = Get-Content $_.FullName -Raw | ConvertFrom-Json; $_.FullName }
```

Live scenario runs require authenticated GitHub Copilot access and may consume Copilot requests.

## References

- Microsoft Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/overview/
- GitHub Copilot provider: https://learn.microsoft.com/en-us/agent-framework/agents/providers/github-copilot
- Foundry Responses and Invocations hosting: https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent
- OpenAI-compatible endpoints: https://learn.microsoft.com/en-us/agent-framework/integrations/openai-endpoints
- Workflow orchestrations: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
