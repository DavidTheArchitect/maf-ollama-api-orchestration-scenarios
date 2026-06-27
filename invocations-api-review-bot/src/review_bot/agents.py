from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

DEFAULT_OLLAMA_MODEL = "qwen3:14b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_TEMPERATURE = 0.2
DEFAULT_OLLAMA_NUM_CTX = 8192
DEFAULT_OLLAMA_MAX_TOKENS = 500
DEFAULT_OLLAMA_KEEP_ALIVE = "10m"
DEFAULT_OLLAMA_THINK = False

_UNSUPPORTED_OLLAMA_CHAT_OPTIONS = {
    "allow_multiple_tool_calls",
    "conversation_id",
    "logit_bias",
    "metadata",
    "store",
    "user",
}


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    instructions: str


@dataclass(frozen=True)
class OllamaAgentConfig:
    model: str
    host: str
    temperature: float
    num_ctx: int
    max_tokens: int
    keep_alive: str
    think: bool

    def default_options(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
            "max_tokens": self.max_tokens,
            "keep_alive": self.keep_alive,
            "think": self.think,
        }


def parse_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false.")


def build_ollama_config(
    *,
    model: str | None = None,
    host: str | None = None,
    temperature: float | None = None,
    num_ctx: int | None = None,
    max_tokens: int | None = None,
    keep_alive: str | None = None,
    think: bool | None = None,
) -> OllamaAgentConfig:
    return OllamaAgentConfig(
        model=model or os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL,
        host=host or os.getenv("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST,
        temperature=temperature
        if temperature is not None
        else float(os.getenv("OLLAMA_TEMPERATURE", str(DEFAULT_OLLAMA_TEMPERATURE))),
        num_ctx=num_ctx if num_ctx is not None else int(os.getenv("OLLAMA_NUM_CTX", str(DEFAULT_OLLAMA_NUM_CTX))),
        max_tokens=max_tokens
        if max_tokens is not None
        else int(os.getenv("OLLAMA_MAX_TOKENS", str(DEFAULT_OLLAMA_MAX_TOKENS))),
        keep_alive=keep_alive or os.getenv("OLLAMA_KEEP_ALIVE") or DEFAULT_OLLAMA_KEEP_ALIVE,
        think=think if think is not None else parse_env_bool("OLLAMA_THINK", DEFAULT_OLLAMA_THINK),
    )


def create_ollama_agent(spec: AgentSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    from agent_framework.ollama import OllamaChatClient

    class ScenarioOllamaChatClient(OllamaChatClient):
        def _prepare_options(self, messages: Any, options: Any) -> dict[str, Any]:
            filtered_options = {
                key: value for key, value in dict(options).items() if key not in _UNSUPPORTED_OLLAMA_CHAT_OPTIONS
            }
            return super()._prepare_options(messages, filtered_options)

    resolved = config or build_ollama_config()
    instructions = f"You are {spec.name}. {spec.instructions}"
    return ScenarioOllamaChatClient(host=resolved.host, model=resolved.model).as_agent(
        name=spec.name,
        description=spec.description,
        instructions=instructions,
        default_options=resolved.default_options(),
        require_per_service_call_history_persistence=True,
    )
