# Scenario Quality & Clean-Code Review

A combined instructor + Python-developer review of all 22 scenarios and the
code that runs them, across both packages (`responses_scenarios`, `invocations_scenarios`), the
API layer, and the notebook generator. Scenario *pattern* quality was already
driven to an 8.67 average by the earlier improvement passes (see
`SCENARIO_RATINGS.md`); this review focuses on the code-quality dimension and
the remaining per-scenario deductions, and every recommendation below has been
implemented (PR references in each section).

This review predates the Scenario 18 primitives lab. That scenario was added
as a capstone-style teaching notebook and is tracked separately in
`SCENARIO_RATINGS.md`.

## A. API layer & helpers (implemented in the "clean code" PR)

| # | Finding | Severity | Fix |
| --- | --- | --- | --- |
| A1 | `except TypeError` wrapped the whole `server.run(port=...)` call in both servers, so a `TypeError` raised *inside* the server was silently swallowed and the server restarted with different config. | Bug | `_run_with_optional_port` binds against `inspect.signature(server.run)` up front; internal `TypeError`s propagate. Covered by tests in both packages. |
| A2 | `_SESSION_TURNS` in `invocations_scenarios/server.py` grew without bound: every session and every turn was retained forever. | Bug (leak) | Bounded: `_MAX_SESSIONS = 64` with oldest-first eviction and `_MAX_TURNS_PER_SESSION = 40` per-session trim, via `_session_history` / `_record_turns`. Covered by tests. |
| A3 | The streaming path re-implemented the sync path's turn-history append — duplicated logic that could drift. | Duplication | Both paths call the single `_record_turns` helper. |
| A4 | `responses_scenarios` buried runtime output extraction inside `notebook_helpers.py` while `invocations_scenarios` had a dedicated `output_formatting.py` — same logic, inconsistent structure. | Structure | `responses_scenarios/output_formatting.py` created; `notebook_helpers` re-exports so existing imports keep working; `workflows.py` imports the canonical module. Cross-*package* duplication is retained deliberately: the two samples are standalone teaching artifacts. |
| A5 | `default_ollama_kwargs()` / `default_ollama_options()` hard-coded values that diverged from the real defaults (`num_ctx 4096` vs the actual `8192`), and had different names across packages. Reference server commands also hard-coded model/token literals. | Lying docs | Both helpers now derive from `build_ollama_config()` (env-aware, single source of truth) and share the `default_ollama_options` name; reference commands use `DEFAULT_OLLAMA_MODEL` / `DEFAULT_OLLAMA_MAX_TOKENS`. |
| A6 | `repo` → `subject` and `changed_files` → `artifacts` request aliases were accepted by `models.py` but absent from the advertised OpenAPI spec. | Docs gap | Aliases documented in `_openapi_spec` and commented at the parse site. Covered by a spec test. |
| A7 | Magic numbers (`80` SSE chunk size, `160` readable-output threshold), a pointless local-assign wrapper in `agent_response_to_text`, and the undocumented `is_object_repr` heuristic. | Minor | Named constants (`_STREAM_CHUNK_CHARS`, `_MIN_READABLE_OUTPUT_CHARS`), wrapper simplified, heuristic's limits documented. |

Also inspected, no change needed: `extract_text`'s recursive walk (complex but
cycle-safe and well-exercised by tests), `models.py` validation branching
(three-way subject fallback now commented), `__main__.py` shims.

## B. Orchestration & executors (implemented in the "scenario quality" PR)

| # | Finding | Severity | Fix |
| --- | --- | --- | --- |
| B1 | `ConcurrentAggregatorExecutor` / `ConcurrentSynthesisGateExecutor` matched agent names to responses **by list index** — the fragile idiom called out in scenario 02's rating. If fan-in ever delivers out of submission order, labels lie. | Fragile | Both executors label by the response's `executor_id` mapped through the agent-name slug, with index fallback. Stub test asserts labels survive a scrambled response order. |
| B2 | `HandoffRouterExecutor.route()` computed the ROUTE directive twice (once in `choose`, once for `route_source`). | Waste/clarity | Single `decide(text) -> (route, source)`; `choose()` retained as a thin wrapper for tests and teaching. |
| B3 | Magentic ledger limits (`10/3/2`) inlined in `build_magentic_workflow` in both packages while the notebooks already name them. | Magic numbers | Module-level `MAGENTIC_LIMITS` in both `workflows.py`, matching the notebook cell. |
| B4 | `PatternName = str` — no typo safety on the pattern field. | Weak typing | `Literal["sequential", "concurrent", "handoff", "group-chat", "magentic"]` in both `types.py`. |

## C. Scenario quality (implemented in the "scenario quality" PR)

| # | Finding | Fix |
| --- | --- | --- |
| C1 | Scenario 01's remaining deduction: sequential stages sometimes re-answer the whole prompt instead of adding their stage's contribution. | `StageGateExecutor` prompt now ends with "Add your stage's contribution; do not repeat the earlier stages." (both packages + notebook template). |
| C2 | Scenario 17's remaining deduction: deterministic partner agents replied with the full fact sheet regardless of the question. | `deterministic_reply(path, question=None)` is question-aware: fact keys matching the question's words are returned (plus notes); the full sheet remains the fallback. Still fully deterministic; threaded through the served agent and the notebook. |
| C3 | Only scenarios 16a–e/17 had `run_sample()` / `python -m` support, and each carried its own copy of the boilerplate. | Shared `scenarios/_runner.py` (`run_sample`, `main`); every scenario module in both packages now has the same three-line runnable tail, and 16/17 lose their duplicated boilerplate. README updated. |

## Ratings impact

The fixes close the documented deductions for scenarios 01, 02, and 17 — see
the addendum in `SCENARIO_RATINGS.md`.
