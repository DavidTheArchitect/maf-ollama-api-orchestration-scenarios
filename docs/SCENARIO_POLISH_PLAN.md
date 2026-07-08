# Plan: Cell-Per-Concept Refactor, Logic Audit, Depth & Polish for All Scenarios

## Context

The 22 learning scenarios (x2 packages, 44 generated notebooks) teach orchestration patterns well after the improvement pass (PRs #6-#9, ratings 7.6 -> 8.4), but the notebooks fight the teaching goal: `scripts/generate_self_contained_notebooks.py` assembles each notebook from 11-13 cells of which three are monoliths - `agent_factory_cell()` (~100 lines), `workflow_cell()` (~250 lines containing **all five** pattern builders regardless of the notebook's pattern), and the inlined MCP server cell (~250-400 lines mixing fixtures and tools). The user wants: (1) cell-per-concept layout for every scenario (matching the convention set in `SCENARIO_17_A2A_PLAN.md`), (2) a logic double-check of every scenario, (3) deeper domain logic so each scenario is sufficiently advanced (**no new framework features** - user's explicit choice), (4) polished docs, and (5) polished teaching visuals (user's explicit choice).

**Status:** implemented. The cell-per-concept generator refactor
(`scripts/generate_self_contained_notebooks.py`), the logic audit, and the
docs/visual polish described below have all landed; the notebooks are now
generated as self-contained, pattern-aware cell sequences. This document is
retained as the design record for that work.

## Workstream A — Cell-per-concept generator refactor

Rework `build_notebook()` (scripts/generate_self_contained_notebooks.py:1999) into a pattern-aware cell sequence (~16–18 cells). Key decompositions:

1. **Split the MCP cell** into (a) a *fixture data* cell — the embedded records/policies/catalog dicts alone, pretty-printed so learners can read and edit them — and (b) a *tool functions* cell that defines the callables and ends with one direct example call (`lookup_enterprise_record("VENDOR-4471")`) so learners see a grounded tool answer before any agent exists.
2. **Split `workflow_cell()` by pattern**: each notebook inlines only its own pattern's machinery, in two cells — (a) shared plumbing (`make_request`, `response_text`, transcript helpers), (b) the pattern's executors/builders with a **direct offline demo**: handoff notebooks call `router.choose()` on sample triage text; group-chat notebooks call `make_group_chat_termination(...)` on fake messages showing mid-cycle vs cycle-end firing; concurrent notebooks demo the labelled aggregation; sequential notebooks demo the stage-gate prompt construction. These demos run with zero LLM calls and give every cell visible output.
3. **Split `agent_factory_cell()`**: AgentSpec/scenario-data cell (renders the roster), then a short factory cell (renders the capability map).
4. **Short build cell**: `build_workflow` for this pattern only — deliberately small, the "orchestration is just wiring" punchline.
5. Keep: title, concept markdown, environment/config (now printing resolved config), flow-diagram pair, live-run pair, what-to-inspect, experiments.

This is the same generator investment Scenario 17's plan requires (per-scenario cell sequences), so 17 plugs into this foundation unchanged.

## Workstream B — Logic double-check (all 22 scenarios, both packages)

Audit checklist applied per scenario, with cheap durable invariants added to tests:

- Route keywords ∩ fixtures: every `route_keywords` term can actually appear in triage output given the fixtures/sample input; `handoff_finisher` / `concurrent_synthesizer` / `termination_phrases` fields consistent with rosters (partially covered by existing tests — extend).
- Every `mcp_tools` name exists on the declared server (check `tests/test_mcp.py` coverage; add if missing), and every tool named in an agent's instructions is in its `mcp_tools` grant.
- Sample inputs reference fixture IDs that exist (VENDOR-4471, ALERT-2298, CLAIM-88120, POLICY-EX-77, FACILITY-DC-EAST, OPP-5001/ACC-3300).
- `learning_goal`/`when_to_use` accurately describe the post-#6–#9 graphs (some prose may still predate the fixes).
- Responses/invocations parity: same structural fields, intentionally different framing only.

## Workstream C — Deeper domain logic (no new framework features)

- **Starters 01–05**: embed concrete working material in sample inputs (a summarized PR diff for 02, an incident timeline with three intertwined symptoms for 05, a release scope table for 01) so agents reason over specifics, not vibes.
- **Enterprise 06–10**: add decision pressure to instructions — conflicting constraints, deadlines, explicit tradeoffs the roles must argue about.
- **MCP 11–15**: add 1–2 fixture wrinkles per scenario so tools surface non-obvious findings (e.g., a second policy that partially conflicts for 11; a claim variant with both a fraud signal *and* a compliance hold to exercise the fraud-first rule in 13; a stale enrichment indicator in 12).
- **16 family**: add a discount-approval tension (requested discount crosses the `Legal (if discount > 20%)` threshold already in `_LEGAL_TERMS`) so pricing/legal debate has stakes in 16d/16e.
- All additions stay deterministic; update `tests/test_mcp.py` / `test_quote_to_cash.py` expectations where fixtures change.

## Workstream D — Docs polish + aesthetics

- **Docs**: make `PATTERN_INSPECT`/`experiments_markdown` scenario-aware where currently pattern-generic (each scenario names its own fixture wrinkle to hunt for); tighten `learning_goal`/`when_to_use` prose found stale in Workstream B; refresh README catalog descriptions and `SCENARIO_RATINGS.md` addendum after the pass.
- **Aesthetics (polished teaching visuals)**: extend the `_APTOS_STYLE` helper into a small self-contained style kit in the generator — styled section headers, callout boxes for instructor notes, agent roster cards, **color-coded per-agent transcript rendering** in live-run output (parse `[AgentName]` labels, deterministic per-agent palette, light/dark safe inline CSS), and themed Mermaid via an init directive. No external assets; all inline.

## Files touched

- `scripts/generate_self_contained_notebooks.py` (main refactor; cell functions + `build_notebook`)
- All 44 notebooks (regenerated, not hand-edited)
- Scenario modules with logic/depth/docs fixes: `responses-api-scenarios/src/responses_scenarios/scenarios/*.py` + mirrors in `invocations-api-scenarios/src/invocations_scenarios/scenarios/*.py`
- Fixture servers where wrinkles land: `src/*/mcp_servers/enterprise_context.py`, `quote_to_cash_context.py` (both packages)
- Tests: `tests/test_notebooks.py` (per-pattern cell assertions: minimum cell count; sequential notebooks must NOT contain `MagenticBuilder`, etc.), `test_mcp.py`, `test_quote_to_cash.py`, `test_workflows.py`
- Docs: `README.md`, `LEARNING_PATH.md`, `SCENARIO_RATINGS.md`

## Verification

- Regenerate all 44 notebooks via the generator; `python -m compileall` both packages + scripts.
- Both offline suites green (currently 48 + 54; new invariant tests added in Workstream B raise these).
- New notebook assertions prove the cell-per-concept layout: every code cell compiles standalone (existing), per-pattern machinery exclusivity, minimum cell counts, and each demo cell's marker present.
- Manual live-run checklist documented for the user (requires local Ollama, unavailable in this environment): one scenario per pattern tier — 01, 07, 13, 14, 16e.

## Implementation sequencing (when later triggered)

Three PRs, self-merged per session convention: **PR1** generator refactor + aesthetics + notebook regeneration + new notebook tests; **PR2** logic audit fixes + fixture depth + test updates; **PR3** docs polish + ratings refresh.
