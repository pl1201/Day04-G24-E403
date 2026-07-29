from __future__ import annotations

import itertools
import json
import os
import re
import time
from typing import Any

from providers.base import ModelResponse, ToolCall


# 429 clears by switching key (free tier is 5 req/min PER KEY); 503 is a shared
# server-side spike, so it needs a short wait instead.
ROTATE_MARKER = "RESOURCE_EXHAUSTED"
BACKOFF_MARKER = "UNAVAILABLE"
EXTRA_ATTEMPTS = 3
BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 8.0


def _gemini_api_keys(base_env: str) -> list[str]:
    """Collect base_env plus numbered siblings (base_env_2, base_env_3, ...) for round-robin rotation."""
    keys = []
    base_value = os.getenv(base_env)
    if base_value:
        keys.append(base_value)
    for name in sorted(os.environ):
        match = re.fullmatch(rf"{re.escape(base_env)}_(\d+)", name)
        if match and os.environ[name]:
            keys.append(os.environ[name])
    return keys


def _to_gemini_declarations(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for item in tools or []:
        function = item.get("function", item)
        declarations.append({
            "name": function["name"],
            "description": function.get("description", ""),
            "parameters": function.get("parameters", {"type": "object", "properties": {}}),
        })
    return declarations


def _to_gemini_contents(messages: list[dict[str, str]]) -> tuple[str | None, list[dict[str, Any]]]:
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
    return ("\n\n".join(system_parts) if system_parts else None), contents


def _part_text(part: Any) -> str | None:
    if hasattr(part, "text"):
        return getattr(part, "text")
    if isinstance(part, dict):
        return part.get("text")
    return None


def _part_function_call(part: Any) -> Any | None:
    if hasattr(part, "function_call"):
        return getattr(part, "function_call")
    if isinstance(part, dict):
        return part.get("function_call")
    return None


def _function_call_name(call: Any) -> str | None:
    if hasattr(call, "name"):
        return getattr(call, "name")
    if isinstance(call, dict):
        return call.get("name")
    return None


def _function_call_args(call: Any) -> dict[str, Any]:
    if hasattr(call, "args"):
        return dict(getattr(call, "args") or {})
    if isinstance(call, dict):
        return dict(call.get("args") or {})
    return {}


class GeminiProvider:
    """Google Gemini API provider with normalized tool_calls output."""

    def __init__(
        self,
        *,
        api_key_env: str = "GEMINI_API_KEY",
        default_model: str = "gemini-3.6-flash",
    ) -> None:
        self.api_key_env = api_key_env
        self.default_model = default_model
        self._key_cycle = itertools.cycle(_gemini_api_keys(api_key_env) or [""])

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install live provider dependency first: pip install google-genai") from exc

        system_instruction, contents = _to_gemini_contents(messages)
        declarations = _to_gemini_declarations(tools)
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if declarations:
            config_kwargs["tools"] = [types.Tool(function_declarations=declarations)]

        attempts = 0
        max_attempts = (len(_gemini_api_keys(self.api_key_env)) or 1) + EXTRA_ATTEMPTS
        last_exc: Exception | None = None
        resp = None
        while attempts < max_attempts:
            api_key = next(self._key_cycle)
            if not api_key:
                raise RuntimeError(f"Missing API key env var: {self.api_key_env}")
            attempts += 1
            try:
                client = genai.Client(api_key=api_key)
                resp = client.models.generate_content(
                    model=model or self.default_model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                break
            except Exception as exc:
                last_exc = exc
                message = str(exc)
                retryable = ROTATE_MARKER in message or BACKOFF_MARKER in message
                if not retryable or attempts >= max_attempts:
                    raise
                if BACKOFF_MARKER in message:
                    time.sleep(min(BACKOFF_SECONDS * attempts, MAX_BACKOFF_SECONDS))
        if resp is None:
            raise last_exc or RuntimeError("Gemini request failed with no available API key")

        text_parts: list[str] = []
        calls: list[ToolCall] = []

        def append_call(function_call: Any) -> None:
            name = _function_call_name(function_call)
            if name:
                calls.append(ToolCall(name=name, args=_function_call_args(function_call)))

        for candidate in getattr(resp, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = _part_text(part)
                if text:
                    text_parts.append(text)
                function_call = _part_function_call(part)
                if function_call:
                    append_call(function_call)

        # Some SDK versions expose function calls directly on the response.
        for function_call in getattr(resp, "function_calls", []) or []:
            append_call(function_call)

        deduped_calls: list[ToolCall] = []
        seen: set[tuple[str, str]] = set()
        for call in calls:
            key = (call.name, json.dumps(call.args, ensure_ascii=False, sort_keys=True))
            if key not in seen:
                seen.add(key)
                deduped_calls.append(call)

        return ModelResponse(text="\n".join(part for part in text_parts if part) or None, tool_calls=deduped_calls, raw=resp)
