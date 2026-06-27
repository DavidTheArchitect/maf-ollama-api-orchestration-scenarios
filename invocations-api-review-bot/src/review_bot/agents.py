from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

#: Top-level package name, used to locate the bundled stdio MCP servers.
_ROOT_PACKAGE = (__package__ or "review_bot").split(".")[0]
#: Registry of local stdio MCP servers, keyed by the name used in ``AgentSpec``.
MCP_SERVER_MODULES: dict[str, str] = {
    "enterprise_context": f"{_ROOT_PACKAGE}.mcp_servers.enterprise_context",
    "quote_to_cash_context": f"{_ROOT_PACKAGE}.mcp_servers.quote_to_cash_context",
}
#: Module path of the local enterprise-context MCP server (run with ``-m``).
ENTERPRISE_MCP_MODULE = MCP_SERVER_MODULES["enterprise_context"]
#: Module path of the local quote-to-cash-context MCP server (run with ``-m``).
QUOTE_TO_CASH_MCP_MODULE = MCP_SERVER_MODULES["quote_to_cash_context"]

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
    mcp_tools: tuple[str, ...] = ()
    mcp_server: str = "enterprise_context"
    code_tools: tuple[str, ...] = ()


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


def build_mcp_tool(spec: AgentSpec) -> Any:
    """Build a local stdio MCP tool restricted to ``spec.mcp_tools``.

    The tool launches the bundled MCP server named by ``spec.mcp_server`` with
    the current interpreter, requires no approval prompts, and exposes only the
    tools the agent is allowed to call.
    """

    from agent_framework import MCPStdioTool

    module = MCP_SERVER_MODULES.get(spec.mcp_server)
    if module is None:
        raise ValueError(
            f"Unknown MCP server '{spec.mcp_server}'. Expected one of: {', '.join(sorted(MCP_SERVER_MODULES))}"
        )
    return MCPStdioTool(
        name=f"{spec.mcp_server.replace('_', '-')}-{spec.name}",
        command=sys.executable,
        args=["-m", module],
        approval_mode="never_require",
        allowed_tools=list(spec.mcp_tools),
    )


#: Backwards-compatible alias for the original single-server helper.
build_enterprise_mcp_tool = build_mcp_tool


def create_ollama_agent(spec: AgentSpec, *, config: OllamaAgentConfig | None = None) -> Any:
    from agent_framework.ollama import OllamaChatClient

    class ScenarioOllamaChatClient(OllamaChatClient):
        def _prepare_options(self, messages: Any, options: Any) -> dict[str, Any]:
            filtered_options = {
                key: value for key, value in dict(options).items() if key not in _UNSUPPORTED_OLLAMA_CHAT_OPTIONS
            }
            return super()._prepare_options(messages, filtered_options)

    from .code_tools import effective_code_tools, resolve_code_tools

    resolved = config or build_ollama_config()
    instructions = f"You are {spec.name}. {spec.instructions}"
    tools: list[Any] = list(resolve_code_tools(effective_code_tools(spec)))
    if spec.mcp_tools:
        tools.append(build_mcp_tool(spec))
    return ScenarioOllamaChatClient(host=resolved.host, model=resolved.model).as_agent(
        name=spec.name,
        description=spec.description,
        instructions=instructions,
        tools=tools or None,
        default_options=resolved.default_options(),
        require_per_service_call_history_persistence=True,
    )
