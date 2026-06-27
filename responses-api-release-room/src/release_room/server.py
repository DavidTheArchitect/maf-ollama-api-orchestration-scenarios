from __future__ import annotations

import argparse
import os

from .scenarios import SCENARIO_IDS, get_scenario, normalize_scenario_id
from .workflows import build_release_workflow


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the release-room Responses API sample.")
    parser.add_argument(
        "--scenario",
        default=os.getenv("RESPONSE_SCENARIO") or os.getenv("RESPONSE_WORKFLOW") or "sequential-release-readiness",
        help=f"Scenario to expose through /responses: {', '.join(SCENARIO_IDS)}.",
    )
    parser.add_argument("--workflow", help="Deprecated alias for --scenario; accepts old pattern names.")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8088")))
    parser.add_argument("--model", default=os.getenv("GITHUB_COPILOT_MODEL") or None)
    return parser


def main() -> None:
    _load_dotenv_if_available()
    args = build_parser().parse_args()
    selected = args.workflow or args.scenario
    scenario_id = normalize_scenario_id(selected)
    scenario = get_scenario(scenario_id)
    os.environ["PORT"] = str(args.port)

    workflow = build_release_workflow(scenario_id, model=args.model)

    from agent_framework_foundry_hosting import ResponsesHostServer

    server = ResponsesHostServer(workflow)
    print(
        f"Serving {scenario.id} ({scenario.pattern}) release-room scenario "
        f"on http://localhost:{args.port}/responses"
    )
    try:
        server.run(port=args.port)
    except TypeError:
        server.run()
