from __future__ import annotations

import argparse
import inspect
import json
import os
from collections.abc import AsyncGenerator
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
from .models import RequestValidationError, parse_invocation_request
from .scenarios import PATTERNS, SCENARIO_IDS
from .workflows import run_invocation

#: Per-session turn history for the optional session-continuity demo. Bounded
#: so a long-running sample server cannot grow without limit: the oldest
#: sessions are evicted first (dict preserves insertion order), and each
#: session keeps only its most recent turns.
_SESSION_TURNS: dict[str, list[str]] = {}
_MAX_SESSIONS = 64
_MAX_TURNS_PER_SESSION = 40


def _session_history(session_id: str | None) -> list[str]:
    """Return (and create) the bounded turn history for ``session_id``."""

    if not session_id:
        return []
    turns = _SESSION_TURNS.setdefault(session_id, [])
    while len(_SESSION_TURNS) > _MAX_SESSIONS:
        oldest = next(iter(_SESSION_TURNS))
        if oldest == session_id:
            break
        del _SESSION_TURNS[oldest]
    return turns


def _record_turns(session_id: str | None, task: str, summary: str) -> None:
    """Append one user/assistant exchange to the session, trimming to the cap."""

    if not session_id:
        return
    turns = _SESSION_TURNS.setdefault(session_id, [])
    turns.extend([f"user: {task}", f"assistant: {summary}"])
    del turns[: max(0, len(turns) - _MAX_TURNS_PER_SESSION)]


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Microsoft Agent Framework Invocations API scenario sample.")
    env_max_tokens = os.getenv("OLLAMA_MAX_TOKENS")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8089")))
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
            f"Defaults to each request scenario's 1000/1500 budget; generic fallback is {DEFAULT_OLLAMA_MAX_TOKENS}."
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


def _openapi_spec() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "MAF Invocations API Scenario Sample", "version": "0.1.0"},
        "paths": {
            "/invocations": {
                "post": {
                    "summary": "Run a structured orchestration scenario.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["task"],
                                    "properties": {
                                        "scenario": {"type": "string", "enum": list(SCENARIO_IDS)},
                                        "pattern": {"type": "string", "enum": list(PATTERNS)},
                                        "task": {"type": "string"},
                                        "subject": {"type": "string"},
                                        "repo": {
                                            "type": "string",
                                            "description": "Accepted alias for 'subject'.",
                                        },
                                        "artifacts": {"type": "array", "items": {"type": "string"}},
                                        "changed_files": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Accepted alias for 'artifacts'.",
                                        },
                                        "constraints": {"type": "array", "items": {"type": "string"}},
                                        "stream": {"type": "boolean"},
                                    },
                                }
                            }
                        },
                    },
                }
            }
        },
    }


def main() -> None:
    _load_dotenv_if_available()
    args = build_parser().parse_args()
    os.environ["PORT"] = str(args.port)

    from azure.ai.agentserver.invocations import InvocationAgentServerHost
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response, StreamingResponse

    app = InvocationAgentServerHost(openapi_spec=_openapi_spec())

    @app.invoke_handler
    async def handle_invoke(request: Request) -> Response:
        try:
            payload = await request.json()
            invocation_request = parse_invocation_request(payload)
        except (json.JSONDecodeError, RequestValidationError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        session_id = getattr(request.state, "session_id", None)
        prior_turns = _session_history(session_id)

        if invocation_request.stream:
            return StreamingResponse(
                _stream_invocation(
                    invocation_request,
                    prior_turns=prior_turns,
                    session_id=session_id,
                    model=args.model,
                    ollama_host=args.ollama_host,
                    temperature=args.temperature,
                    num_ctx=args.num_ctx,
                    max_tokens=args.max_tokens,
                    keep_alive=args.keep_alive,
                    think=args.think,
                ),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

        response = await run_invocation(
            invocation_request,
            session_id=session_id,
            previous_turns=prior_turns,
            model=args.model,
            ollama_host=args.ollama_host,
            temperature=args.temperature,
            num_ctx=args.num_ctx,
            max_tokens=args.max_tokens,
            keep_alive=args.keep_alive,
            think=args.think,
        )
        _record_turns(session_id, invocation_request.task, response.summary)
        return JSONResponse(response.to_dict())

    print(f"Serving Invocations API scenarios with Ollama model {args.model} on http://localhost:{args.port}/invocations")
    _run_with_optional_port(app, args.port)


async def _stream_invocation(
    invocation_request,
    *,
    prior_turns: list[str],
    session_id: str | None,
    model: str | None,
    ollama_host: str | None,
    temperature: float | None,
    num_ctx: int | None,
    max_tokens: int | None,
    keep_alive: str | None,
    think: bool | None,
) -> AsyncGenerator[bytes]:
    response = await run_invocation(
        invocation_request,
        session_id=session_id,
        previous_turns=prior_turns,
        model=model,
        ollama_host=ollama_host,
        temperature=temperature,
        num_ctx=num_ctx,
        max_tokens=max_tokens,
        keep_alive=keep_alive,
        think=think,
    )
    _record_turns(session_id, invocation_request.task, response.summary)

    for token in _chunk_text(response.summary):
        yield f"data: {json.dumps({'token': token})}\n\n".encode("utf-8")
    yield b"event: done\ndata: {}\n\n"


#: Characters per streamed SSE token chunk: small enough that streaming is
#: visibly incremental in a terminal, large enough to keep event overhead low.
_STREAM_CHUNK_CHARS = 80


def _chunk_text(text: str, *, size: int = _STREAM_CHUNK_CHARS) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + size] for index in range(0, len(text), size)]


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
