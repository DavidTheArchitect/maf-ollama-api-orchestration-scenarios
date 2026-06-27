# Responses API Release Room

This sample hosts five Microsoft Agent Framework multi-agent scenarios behind the OpenAI-compatible Responses API.

Use this shape when the caller is a chat UI, OpenAI-compatible SDK, DevUI-style frontend, or anything that benefits from standard `/responses` semantics.

## How Scenario Selection Works

The request body stays Responses-compatible. Choose the scenario when starting the server:

```powershell
python -m release_room --scenario sequential-release-readiness --port 8088
```

Supported scenarios:

| Scenario | Pattern | Agents | Learning focus |
| --- | --- | ---: | --- |
| `sequential-release-readiness` | Sequential | 5 | A fixed release-readiness pipeline where each agent transforms the prior output. |
| `concurrent-pr-review` | Concurrent | 5 | One chat request fans out to independent specialist reviewers. |
| `handoff-support-triage` | Handoff | 5 | A triage agent routes a conversational issue to the right specialist. |
| `group-chat-launch-council` | Group chat | 5 | A visible council iteratively critiques and refines a launch decision. |
| `magentic-incident-response` | Magentic | 6 | A manager agent dynamically coordinates specialists for open-ended incident work. |

## Install

```powershell
ollama pull qwen3:14b
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
python -m release_room --scenario group-chat-launch-council --model qwen3:14b --port 8088
```

Invoke with a normal Responses-style payload:

```powershell
(Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\group-chat-launch-council.json -Raw)).Content
```

Streaming:

```powershell
python -m release_room --scenario magentic-incident-response --model qwen3:14b --port 8088
Invoke-WebRequest -Uri http://localhost:8088/responses -Method POST -ContentType "application/json" -Body (Get-Content .\samples\magentic-incident-response-streaming.json -Raw)
```

## When Responses API Fits

- You want a standard OpenAI-compatible endpoint.
- Your client is conversational and should not know about internal orchestration details.
- You want to swap orchestration behind a stable `/responses` contract.
- You want standard Responses streaming and conversation behavior.

## Notes

- This sample uses the native `agent-framework-ollama` provider, so model calls stay local.
- Use `--ollama-host`, `--temperature`, `--num-ctx`, `--keep-alive`, and `--think` to tune the local Ollama runtime without changing the API shape.
- Ollama supports local function tools through Agent Framework, but it does not provide hosted tools such as hosted code interpreter, file search, web search, or hosted MCP.
- `--workflow` still works as a deprecated alias for the old sample and maps pattern names to the matching scenario.
