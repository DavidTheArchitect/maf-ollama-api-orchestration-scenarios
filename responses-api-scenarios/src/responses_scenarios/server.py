from __future__ import annotations

import argparse
import inspect
import os
from typing import Any

from .agents import (
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_KEEP_ALIVE,
    DEFAULT_OLLAMA_MAX_TOKENS,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_NUM_CTX,
    DEFAULT_OLLAMA_TEMPERATURE,
    DEFAULT_OLLAMA_THINK,
    parse_env_bool,
)
from .scenarios import SCENARIO_IDS, get_scenario, normalize_scenario_id
from .workflows import build_responses_workflow


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Microsoft Agent Framework Responses API scenario sample.")
    env_max_tokens = os.getenv("OLLAMA_MAX_TOKENS")
    parser.add_argument(
        "--scenario",
        default=os.getenv("RESPONSE_SCENARIO") or os.getenv("RESPONSE_WORKFLOW") or "sequential-release-readiness",
        help=f"Scenario to expose through /responses: {', '.join(SCENARIO_IDS)}.",
    )
    parser.add_argument("--workflow", help="Deprecated alias for --scenario; accepts old pattern names.")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8088")))
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL)
    parser.add_argument("--ollama-host", default=os.getenv("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST)
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.getenv("OLLAMA_TEMPERATURE", str(DEFAULT_OLLAMA_TEMPERATURE))),
    )
    parser.add_argument("--num-ctx", type=int, default=int(os.getenv("OLLAMA_NUM_CTX", str(DEFAULT_OLLAMA_NUM_CTX))))
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(env_max_tokens) if env_max_tokens else None,
        help=(
            "Maximum tokens each local Ollama agent may generate per turn. "
            f"Defaults to the selected scenario's 1000/1500 budget; generic fallback is {DEFAULT_OLLAMA_MAX_TOKENS}."
        ),
    )
    parser.add_argument("--keep-alive", default=os.getenv("OLLAMA_KEEP_ALIVE") or DEFAULT_OLLAMA_KEEP_ALIVE)
    parser.add_argument(
        "--think",
        action=argparse.BooleanOptionalAction,
        default=parse_env_bool("OLLAMA_THINK", DEFAULT_OLLAMA_THINK),
        help="Enable or disable Ollama thinking mode for models that support it.",
    )
    return parser


def main() -> None:
    _load_dotenv_if_available()
    args = build_parser().parse_args()
    selected = args.workflow or args.scenario
    scenario_id = normalize_scenario_id(selected)
    scenario = get_scenario(scenario_id)
    os.environ["PORT"] = str(args.port)

    workflow = build_responses_workflow(
        scenario_id,
        model=args.model,
        ollama_host=args.ollama_host,
        temperature=args.temperature,
        num_ctx=args.num_ctx,
        max_tokens=args.max_tokens,
        keep_alive=args.keep_alive,
        think=args.think,
    )

    from agent_framework import WorkflowAgent
    from agent_framework_foundry_hosting import ResponsesHostServer

    agent = WorkflowAgent(
        workflow,
        name=f"responses-api-{scenario.id}",
        description=f"{scenario.title} workflow exposed through the Responses API.",
    )
    server = ResponsesHostServer(agent)
    print(
        f"Serving {scenario.id} ({scenario.pattern}) Responses API scenario "
        f"with Ollama model {args.model} on http://localhost:{args.port}/responses"
    )
    _run_with_optional_port(server, args.port)


def _run_with_optional_port(server: Any, port: int) -> None:
    """Start the host, passing ``port`` only when the signature accepts it.

    Binding is checked up front so a ``TypeError`` raised *inside* the server
    propagates instead of being mistaken for an unsupported keyword.
    """

    try:
        inspect.signature(server.run).bind(port=port)
    except TypeError:
        server.run()
        return
    server.run(port=port)
