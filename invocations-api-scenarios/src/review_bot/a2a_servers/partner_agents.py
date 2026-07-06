"""Local, deterministic ``partner-agents`` A2A server.

This module hosts the two *partner-organization* agents for the Scenario 17
group chat over the A2A (Agent2Agent) protocol. It follows the same philosophy
as the bundled MCP servers:

* No credentials, no writes, localhost only.
* Deterministic by default: the partner agents answer from embedded fixture
  facts, so tests and notebooks are reproducible with zero LLM calls.
* Optional ``--ollama`` mode serves instruction-led LLM agents instead, for a
  true agent-to-agent experience.

Run it directly with::

    python -m review_bot.a2a_servers.partner_agents --port 8765

Each partner agent is mounted under its own path and serves its agent card at
``<base>/<path>/.well-known/agent-card.json``:

* ``/partner-solutions`` -- ``PartnerSolutionsAgent`` (the ISV partner)
* ``/compliance`` -- ``ExternalComplianceAgent`` (the external audit firm)

Clients attach with ``agent_framework.a2a.A2AAgent(url=...)``.
"""

from __future__ import annotations

import argparse
import re
import socket
import threading
import time
from typing import Any

SERVER_NAME = "partner-agents"
DEFAULT_PORT = 8765

#: Embedded partner facts. Engineered so the launch-review debate has stakes:
#: the certification expires mid launch window and one compliance finding is
#: still open.
PARTNER_FIXTURES: dict[str, dict[str, Any]] = {
    "partner-solutions": {
        "organization": "Fabrikam Integrations (ISV partner)",
        "integration_certification_expires": "2026-07-20",
        "launch_window": "2026-07-15 to 2026-07-31",
        "nightly_integration_tests": "47 passing, 1 failing (bulk-export, since Tuesday)",
        "connector_version": "2.3.1",
        "notes": "Certification expires mid launch window; the renewal audit is booked for 2026-07-18.",
    },
    "compliance": {
        "organization": "Meridian Assurance (external audit firm)",
        "soc2_status": "current",
        "joint_data_processing_addendum": "signed",
        "open_findings": 1,
        "open_finding_detail": "Partner telemetry retention is 120 days; the joint standard requires 90.",
        "notes": "The open finding needs a remediation date before joint go-live.",
    },
}

#: The two partner seats this server exposes, keyed by mount path.
PARTNER_AGENTS: dict[str, dict[str, str]] = {
    "partner-solutions": {
        "name": "PartnerSolutionsAgent",
        "description": "ISV partner agent: argues partner-side integration readiness over A2A.",
        "instructions": (
            "You represent the ISV partner in a joint launch review. Argue partner-side readiness "
            "strictly from your organization's facts: certification dates, connector version, and "
            "nightly integration test results. Flag anything that conflicts with the launch window."
        ),
    },
    "compliance": {
        "name": "ExternalComplianceAgent",
        "description": "External audit firm agent: argues certification and compliance status over A2A.",
        "instructions": (
            "You represent the external audit firm in a joint launch review. Argue compliance "
            "readiness strictly from your organization's facts: SOC 2 status, the joint data "
            "processing addendum, and open findings. Insist on remediation dates where needed."
        ),
    },
}


def deterministic_reply(path: str, question: str | None = None) -> str:
    """The fixture-grounded answer a partner agent gives, with zero LLM calls.

    Question-aware but still deterministic: fact keys whose words overlap the
    question are returned (plus the notes); with no overlap or no question,
    the full fact sheet is the fallback.
    """

    facts = PARTNER_FIXTURES[path]
    spec = PARTNER_AGENTS[path]
    selected = {key: value for key, value in facts.items() if key != "organization"}
    if question:
        words = {word for word in re.findall(r"[a-z0-9]+", question.lower()) if len(word) > 3}
        matched = {
            key: value for key, value in selected.items() if set(key.split("_")) & words
        }
        if matched:
            matched.setdefault("notes", facts["notes"])
            selected = matched
    lines = [f"{spec['name']} ({facts['organization']}) reports:"]
    for key, value in selected.items():
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def _message_text(messages: Any) -> str:
    """Best-effort text of the incoming A2A message(s) for fact selection."""

    if messages is None:
        return ""
    if isinstance(messages, str):
        return messages
    if isinstance(messages, (list, tuple)):
        return " ".join(_message_text(message) for message in messages)
    return getattr(messages, "text", "") or ""


def _make_local_agent(path: str, *, use_ollama: bool = False) -> Any:
    """The agent served behind the A2A endpoint for ``path``."""

    spec = PARTNER_AGENTS[path]
    if use_ollama:
        from ..agents import AgentSpec, create_ollama_agent

        facts = "\n".join(f"{k}: {v}" for k, v in PARTNER_FIXTURES[path].items())
        return create_ollama_agent(
            AgentSpec(
                spec["name"],
                spec["description"],
                f"{spec['instructions']}\n\nYour organization's facts:\n{facts}",
            )
        )

    from agent_framework import AgentResponse, BaseAgent, Message

    class DeterministicPartnerAgent(BaseAgent):
        async def run(self, messages=None, *, session=None, **kwargs):
            reply = deterministic_reply(path, _message_text(messages))
            return AgentResponse(messages=[Message(role="assistant", contents=[reply])])

        async def run_stream(self, messages=None, *, session=None, **kwargs):
            yield await self.run(messages, session=session, **kwargs)

    return DeterministicPartnerAgent(name=spec["name"], description=spec["description"])


def _build_partner_routes(path: str, base_url: str, *, use_ollama: bool = False) -> Any:
    """Routes for one partner agent: card + JSON-RPC endpoint under ``/<path>``."""

    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

    from agent_framework.a2a import A2AExecutor

    spec = PARTNER_AGENTS[path]
    card = AgentCard(
        name=spec["name"],
        description=spec["description"],
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"{base_url}/{path}", protocol_binding="JSONRPC")],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id=f"{path}-launch-review",
                name="Joint launch review",
                description=spec["description"],
                tags=["launch-review", "a2a"],
            )
        ],
    )
    executor = A2AExecutor(_make_local_agent(path, use_ollama=use_ollama))
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore(), agent_card=card)
    # Flat prefixed routes (no Mount): the JSON-RPC endpoint lives at exactly
    # /<path>, so clients never hit a trailing-slash redirect.
    return create_agent_card_routes(
        card, card_url=f"/{path}/.well-known/agent-card.json"
    ) + create_jsonrpc_routes(handler, rpc_url=f"/{path}")


def build_partner_app(base_url: str, *, use_ollama: bool = False) -> Any:
    """Starlette app hosting every partner agent under its own path prefix."""

    from starlette.applications import Starlette

    routes = []
    for path in PARTNER_AGENTS:
        routes.extend(_build_partner_routes(path, base_url, use_ollama=use_ollama))
    return Starlette(routes=routes)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class PartnerA2AServer:
    """In-process uvicorn host for the partner agents on an ephemeral port.

    Usable as a context manager so notebooks and tests need no second terminal::

        with PartnerA2AServer() as server:
            agent = A2AAgent(url=server.partner_urls["PartnerSolutionsAgent"])
    """

    def __init__(self, port: int | None = None, *, use_ollama: bool = False) -> None:
        self.port = port or _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._use_ollama = use_ollama
        self._server: Any = None
        self._thread: threading.Thread | None = None

    @property
    def partner_urls(self) -> dict[str, str]:
        return {spec["name"]: f"{self.base_url}/{path}" for path, spec in PARTNER_AGENTS.items()}

    def start(self, timeout: float = 10.0) -> "PartnerA2AServer":
        import uvicorn

        app = build_partner_app(self.base_url, use_ollama=self._use_ollama)
        self._server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error")
        )
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.time() + timeout
        while not self._server.started:
            if time.time() > deadline:
                raise RuntimeError(f"Partner A2A server did not start on {self.base_url}.")
            time.sleep(0.05)
        return self

    def stop(self, timeout: float = 5.0) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def __enter__(self) -> "PartnerA2AServer":
        return self.start()

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()


def main() -> None:
    """Serve the partner agents (blocking) for live scenario runs."""

    import uvicorn

    parser = argparse.ArgumentParser(description="Serve the Scenario 17 partner agents over A2A.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--ollama", action="store_true", help="Serve LLM-backed partner agents via Ollama.")
    args = parser.parse_args()
    base_url = f"http://127.0.0.1:{args.port}"
    app = build_partner_app(base_url, use_ollama=args.ollama)
    for name, url in {s["name"]: f"{base_url}/{p}" for p, s in PARTNER_AGENTS.items()}.items():
        print(f"{name}: {url}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
