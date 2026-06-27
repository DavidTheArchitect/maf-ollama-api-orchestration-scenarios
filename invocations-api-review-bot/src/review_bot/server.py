from __future__ import annotations

import argparse
import json
import os
from collections.abc import AsyncGenerator

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
from .models import RequestValidationError, parse_review_request
from .scenarios import PATTERNS, SCENARIO_IDS
from .workflows import run_review

_SESSION_TURNS: dict[str, list[str]] = {}


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the review-bot Invocations API sample.")
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
        default=int(os.getenv("OLLAMA_MAX_TOKENS", str(DEFAULT_OLLAMA_MAX_TOKENS))),
        help="Maximum tokens each local Ollama agent may generate per turn.",
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
        "info": {"title": "MAF Review Bot Invocations Sample", "version": "0.1.0"},
        "paths": {
            "/invocations": {
                "post": {
                    "summary": "Run a structured repository review job.",
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
                                        "artifacts": {"type": "array", "items": {"type": "string"}},
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
            review_request = parse_review_request(payload)
        except (json.JSONDecodeError, RequestValidationError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        session_id = getattr(request.state, "session_id", None)
        prior_turns = _SESSION_TURNS.setdefault(session_id, []) if session_id else []

        if review_request.stream:
            return StreamingResponse(
                _stream_review(
                    review_request,
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

        response = await run_review(
            review_request,
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
        if session_id:
            prior_turns.extend([f"user: {review_request.task}", f"assistant: {response.summary}"])
        return JSONResponse(response.to_dict())

    print(f"Serving review-bot invocations with Ollama model {args.model} on http://localhost:{args.port}/invocations")
    try:
        app.run(port=args.port)
    except TypeError:
        app.run()


async def _stream_review(
    review_request,
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
    response = await run_review(
        review_request,
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
    if session_id:
        prior_turns.extend([f"user: {review_request.task}", f"assistant: {response.summary}"])

    for token in _chunk_text(response.summary):
        yield f"data: {json.dumps({'token': token})}\n\n".encode("utf-8")
    yield b"event: done\ndata: {}\n\n"


def _chunk_text(text: str, *, size: int = 80) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + size] for index in range(0, len(text), size)]
