"""
Patch generate_self_contained_notebooks.py with learning improvements.
Safe to run multiple times (idempotent guard on anchors).
"""
from __future__ import annotations
import re
import pathlib
import textwrap

TARGET = pathlib.Path(__file__).parent / "generate_self_contained_notebooks.py"


# ---------------------------------------------------------------------------
# 1. New top-level constants (added after PATTERN_ANATOMY)
# ---------------------------------------------------------------------------
NEW_CONSTANTS = textwrap.dedent("""\

    PATTERN_LIVE_RUN_INTRO = {
        "sequential": (
            "Each agent output is captured by a `StageGateExecutor` and appended to a growing "
            "transcript. The next agent receives both the original prompt and the accumulated "
            "work so far. The final cell prints the complete stage-by-stage log."
        ),
        "concurrent": (
            "The request fans out to all specialists simultaneously. A `ConcurrentAggregatorExecutor` "
            "waits for every response, then labels each contribution and joins them. "
            "Execution order inside the fan-out is non-deterministic."
        ),
        "handoff": (
            "Triage runs first. A `HandoffRouterExecutor` reads the triage text, scores each "
            "specialist keyword list against it, and forwards the request to the highest-scoring "
            "specialist. The output shows the route taken and the specialist response."
        ),
        "group-chat": (
            "Participants speak in round-robin order. The termination function fires when an "
            "approved recommendation appears or after seven assistant turns. Intermediate outputs "
            "from each participant are surfaced alongside the final transcript."
        ),
        "magentic": (
            "The manager agent plans, delegates to specialists, and replans if work stalls or "
            "reaches a reset limit. With `max_round_count=10`, `max_stall_count=3`, and "
            "`max_reset_count=2`, there is room to iterate. Allow extra time -- this pattern "
            "runs more LLM calls than the others."
        ),
    }


    PATTERN_INSPECT = {
        "sequential": (
            "Compare the first stage output to the final editor output. Later stages should "
            "build on prior work, not repeat it -- each `StageGateExecutor` carries the full "
            "transcript forward. If a stage ignores prior context, inspect its instructions "
            "and the gate prompt to see exactly what the agent received."
        ),
        "concurrent": (
            "Check that each labelled specialist contribution is non-overlapping. Because agents "
            "receive the same input and run independently, their findings should be additive, "
            "not redundant. If two specialists repeat each other, their roles or instructions "
            "may need tighter scoping."
        ),
        "handoff": (
            "Verify the route matches the triage intent. The `HandoffRouterExecutor` picks the "
            "specialist with the most keyword hits against the triage text. Try rewording the "
            "input toward a different specialist domain and rerun -- the route should change. "
            "Inspect `ctx.get_state('route')` for the chosen executor id."
        ),
        "group-chat": (
            "Read the transcript chronologically. Later turns should respond to earlier critiques "
            "rather than restarting the discussion. The termination function fires on 'approved' "
            "plus 'recommendation' in the same message, or after seven assistant turns -- check "
            "which condition fired and why."
        ),
        "magentic": (
            "Follow the specialist outputs to reconstruct the manager delegation path. If the "
            "manager replanned, you will see the same specialist invoked more than once or a "
            "different specialist substituted mid-run. A stall (no progress for max_stall_count "
            "rounds) triggers a reset; a second stall terminates the workflow."
        ),
    }
""")


# ---------------------------------------------------------------------------
# 2. _agent_tools_label helper + improved title_markdown
# ---------------------------------------------------------------------------
OLD_TITLE_FUNC = '''\
def title_markdown(project: dict[str, str], scenario: Any) -> str:
    return f"""
    # {scenario.title}

    | Field | Value |
    | --- | --- |
    | Scenario id | `{scenario.id}` |
    | Pattern | `{scenario.pattern}` |
    | API | `{project['api_name']}` |

    {scenario.learning_goal}
    """'''

NEW_TITLE_FUNC = '''\
def _agent_tools_label(agent: Any) -> str:
    """Short display string of tools used by an agent, for the agent roster table."""
    code_tools = list(getattr(agent, "code_tools", ()) or ())
    mcp_tools = list(getattr(agent, "mcp_tools", ()) or ())
    parts: list[str] = []
    if code_tools:
        parts.append(", ".join("`" + t + "`" for t in code_tools))
    else:
        parts.append("_role defaults_")
    if mcp_tools:
        parts.append("MCP: " + ", ".join("`" + t + "`" for t in mcp_tools))
    return " \xb7 ".join(parts)


def title_markdown(project: dict[str, str], scenario: Any) -> str:
    return f"""
    # {scenario.title}

    | Field | Value |
    | --- | --- |
    | Scenario id | `{scenario.id}` |
    | Pattern | `{scenario.pattern}` |
    | API | `{project['api_name']}` |

    **Learning goal:** {scenario.learning_goal}

    > {scenario.when_to_use}
    """'''


# ---------------------------------------------------------------------------
# 3. Improved concept_markdown
#    Pre-compute anatomy table and agent roster at generation time (no nested
#    f-string escaping needed inside the generator return value).
# ---------------------------------------------------------------------------
OLD_CONCEPT_FUNC_START = "def concept_markdown(project: dict[str, str], scenario: Any) -> str:"
OLD_CONCEPT_FUNC_END = '    {json.dumps(PATTERN_ANATOMY[scenario.pattern], indent=2)}\n    """'

NEW_CONCEPT_FUNC = '''\
def concept_markdown(project: dict[str, str], scenario: Any) -> str:
    concept, best_fit = PATTERN_DOCS[scenario.pattern]

    if project["sample_attr"] == "sample_input":
        api_note = (
            "**Responses API -- startup-selected scenario shape.** "
            "The scenario and orchestration pattern are wired in at server start. "
            "Each client request uses the standard OpenAI-compatible `/responses` body -- "
            "a plain chat-style input. The client never specifies which agents run; "
            "the server owns the orchestration entirely."
        )
    else:
        api_note = (
            "**Invocations API -- per-request job payload shape.** "
            "Each request body carries `scenario`, `pattern`, `task`, `artifacts`, and "
            "`constraints`. The caller controls which orchestration runs per invocation. "
            "This fits webhooks, CI pipelines, schedulers, and service-to-service calls "
            "where the task definition changes with every request."
        )

    if scenario.id.startswith("scenario-16-quote-to-cash"):
        story = (
            "This is a Scenario 16 quote-to-cash variant. The same six business roles "
            "(CRM trigger, customer context, SKU discovery, product fit, pricing and legal, "
            "quote generation) appear in every Scenario 16 notebook -- only the orchestration "
            "pattern changes. Compare notebooks 16a-16e to see how the same roles behave "
            "under sequential, concurrent, handoff, group-chat, and magentic coordination."
        )
    elif scenario_uses_mcp(scenario):
        story = (
            "This is an enterprise scenario grounded by deterministic MCP context tools. "
            "In production those tools are served by a FastMCP stdio subprocess; "
            "this notebook inlines the same functions as plain callables so it runs "
            "without a local package or subprocess."
        )
    else:
        story = (
            "This is a starter scenario. The domain is intentionally lightweight "
            "so the orchestration mechanics are easy to trace before the enterprise "
            "and quote-to-cash notebooks layer in MCP tool calls and richer context."
        )

    anatomy = PATTERN_ANATOMY[scenario.pattern]
    anatomy_rows = "\\n".join([
        "| Dimension | Detail |",
        "| --- | --- |",
        "| Control flow | " + anatomy["control_flow"] + " |",
        "| Coordination | " + anatomy["coordination"] + " |",
        "| Output | " + anatomy["output_behavior"] + " |",
        "| Best when | " + anatomy["best_when"] + " |",
    ])

    agent_header = "| Agent | Role | Tools |\\n| --- | --- | --- |"
    agent_lines = "\\n".join(
        "| `" + a.name + "` | " + a.description + " | " + _agent_tools_label(a) + " |"
        for a in scenario.agents
    )
    agent_table = agent_header + "\\n" + agent_lines

    pattern_heading = scenario.pattern.replace("-", " ").title()

    return f"""
    ## Pattern: {pattern_heading}

    {concept}

    {best_fit}

    ## API Shape

    {api_note}

    {story}

    ## Pattern Anatomy

    {anatomy_rows}

    ## Agent Roster

    {agent_table}

    > **Instructor note:** Every agent receives deterministic Python tool functions.
    > Tools labelled _role defaults_ are assigned by keyword matching on the agent name
    > and description. MCP tools map to the inlined context functions in the cell below.
    """'''


# ---------------------------------------------------------------------------
# 4. New helper functions inserted before experiments_markdown
# ---------------------------------------------------------------------------
NEW_HELPER_FUNCS = '''\
def flow_diagram_markdown(project: dict[str, str], scenario: Any) -> str:
    pattern = scenario.pattern
    n = len(scenario.agents)
    if pattern == "sequential":
        shape = "a linear chain of " + str(n) + " stages with a stage-gate executor between each pair"
    elif pattern == "concurrent":
        shape = "a fan-out to " + str(n) + " specialists and a labelled fan-in aggregation"
    elif pattern == "handoff":
        shape = "a triage node routing to one of " + str(n - 1) + " specialists via keyword scoring"
    elif pattern == "group-chat":
        shape = str(n) + " participants in a round-robin loop with a coded termination function"
    else:
        shape = "a manager agent delegating to " + str(n - 1) + " specialists with progress-ledger replanning"
    boundary = project["api_boundary"]
    return f"""
    ## Flow Diagram

    The diagram below shows {shape} attached to the {boundary}.
    Solid arrows are orchestration edges. Dashed arrows (`-.->`) are tool calls.
    MCP tool nodes use a stadium shape; code tool nodes use a parallelogram.
    """


def live_run_markdown(scenario: Any) -> str:
    intro = PATTERN_LIVE_RUN_INTRO[scenario.pattern]
    return f"""
    ## Live Run

    {intro}

    > **Instructor note:** `qwen3:14b` runs with `think: False` by default (extended reasoning off).
    > Set `OLLAMA_THINK=true` before the environment cell to enable chain-of-thought reasoning --
    > useful when debugging unexpected routing decisions or tool call sequences.
    """


def post_run_markdown(scenario: Any) -> str:
    inspect = PATTERN_INSPECT[scenario.pattern]
    return f"""
    ## What to Inspect

    {inspect}
    """


'''


def apply(src: str) -> str:
    # Idempotency guard
    if "PATTERN_LIVE_RUN_INTRO" in src:
        print("Already patched -- skipping.")
        return src

    # ---- 1. New constants after PATTERN_ANATOMY block ----
    anchor_const = "\n\ndef cell_source"
    assert anchor_const in src, "Anchor for constants not found"
    src = src.replace(anchor_const, NEW_CONSTANTS + "\n\ndef cell_source", 1)

    # ---- 2. Replace title_markdown (insert _agent_tools_label before it) ----
    assert OLD_TITLE_FUNC in src, "OLD_TITLE_FUNC not found"
    src = src.replace(OLD_TITLE_FUNC, NEW_TITLE_FUNC, 1)

    # ---- 3. Replace concept_markdown ----
    # Find by start + end anchors
    start_idx = src.index(OLD_CONCEPT_FUNC_START)
    end_idx = src.index(OLD_CONCEPT_FUNC_END, start_idx) + len(OLD_CONCEPT_FUNC_END)
    src = src[:start_idx] + NEW_CONCEPT_FUNC + src[end_idx:]

    # ---- 4. Insert helper functions before experiments_markdown ----
    anchor_exp = "\ndef experiments_markdown"
    assert anchor_exp in src, "experiments_markdown anchor not found"
    src = src.replace(anchor_exp, "\n\n" + NEW_HELPER_FUNCS + "def experiments_markdown", 1)

    # ---- 5. Update build_notebook to use new functions ----
    old_flow = '            md("## Flow Diagram"),'
    new_flow = '            md(flow_diagram_markdown(project, scenario)),'
    assert old_flow in src, "old flow diagram line not found"
    src = src.replace(old_flow, new_flow, 1)

    old_live = '            md("## Live Run"),'
    new_live = '            md(live_run_markdown(scenario)),'
    assert old_live in src, "old live run line not found"
    src = src.replace(old_live, new_live, 1)

    old_after = '            code(live_run_cell()),\n            md(experiments_markdown'
    new_after = '            code(live_run_cell()),\n            md(post_run_markdown(scenario)),\n            md(experiments_markdown'
    assert old_after in src, "live_run_cell anchor for post_run not found"
    src = src.replace(old_after, new_after, 1)

    return src


def main() -> None:
    src = TARGET.read_text(encoding="utf-8")
    # Normalize CRLF -> LF for processing, restore at end
    crlf = "\r\n" in src
    src_lf = src.replace("\r\n", "\n")

    patched_lf = apply(src_lf)

    if crlf:
        patched = patched_lf.replace("\n", "\r\n")
    else:
        patched = patched_lf

    TARGET.write_text(patched, encoding="utf-8")
    print(f"Patched {TARGET}")
    n_before = src.replace("\r\n", "\n").count("\n")
    n_after = patched_lf.count("\n")
    print(f"Lines: {n_before} -> {n_after} (+{n_after - n_before})")


if __name__ == "__main__":
    main()
