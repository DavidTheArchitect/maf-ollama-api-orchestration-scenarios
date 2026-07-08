# Self-Contained MAF Scenario Notebooks

## Current Structure

- `responses-api-scenarios/` contains the Responses API scenario notebooks and the optional `responses_scenarios` reference package.
- `invocations-api-scenarios/` contains the Invocations API scenario notebooks and the optional `invocations_scenarios` reference package.
- Each folder keeps its `src/` package and unit tests as reference implementations, but the notebooks do not import those local packages.

## Notebook Contract

Every notebook is generated as a self-contained scenario:

- imports only third-party runtime packages such as `agent_framework`, `agent_framework.ollama`, and `IPython`;
- defines Aptos notebook styling inline;
- defaults to `OLLAMA_MODEL=qwen3:14b` and `OLLAMA_HOST=http://localhost:11434`;
- inlines the agent factory, agent roster, orchestration graph, diagram helper, live run cell, and any domain tools needed for that scenario;
- uses plain in-notebook function tools for enterprise and quote-to-cash context, with a note that the reference packages expose equivalent MCP stdio servers for production-style wiring;
- keeps outputs cleared for source control.

## Generation And Validation

Regenerate all notebooks:

```powershell
python scripts\generate_self_contained_notebooks.py
```

Execute all notebooks against local Ollama:

```powershell
.\scripts\execute_notebooks.ps1
```

The execution harness expects `ollama serve` to be reachable and `qwen3:14b` to be pulled. It runs all 44 notebooks with nbconvert and a 20-minute timeout per notebook.

Run the reference test suites from each project folder:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Maintenance Notes

- Update scenario behavior in the reference package first, then regenerate notebooks.
- Keep notebook tests focused on self-contained execution: no local package imports, no `sys.path` bootstrapping, and no committed outputs.
- Preserve the five orchestration patterns and the mirrored scenario ids across both API folders.
