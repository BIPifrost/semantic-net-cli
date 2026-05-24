"""Provide a shared LLM client wrapper for all agents."""

from __future__ import annotations

from typing import Any, Callable

from openai import OpenAI

from semantic_net_cli.llm.config_loader import AgentLLMSettings


Transport = Callable[[dict[str, Any]], dict[str, Any]]


class LLMClient:
    """Shared wrapper used by all agents for LLM requests."""

    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or self._default_transport

    def invoke(
        self,
        *,
        agent_name: str,
        settings: AgentLLMSettings,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Send one request using resolved agent settings."""

        payload = {
            "agent_name": agent_name,
            "provider": settings.provider,
            "api_format": settings.api_format,
            "model": settings.model,
            "api_key": settings.api_key,
            "base_url": settings.base_url,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "thinking_enabled": settings.thinking_enabled,
            "reasoning_effort": settings.reasoning_effort,
            "stream": settings.stream,
            "response_format": settings.response_format,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
        return self._transport(payload)

    @staticmethod
    def _default_transport(payload: dict[str, Any]) -> dict[str, Any]:
        """Default transport issues a live request using configured provider settings."""

        api_format = payload.get("api_format", "openai")
        if api_format != "openai":
            raise RuntimeError(
                f"Unsupported live api_format: {api_format}. "
                "Only openai-compatible transport is implemented in this prototype."
            )

        client = OpenAI(
            api_key=payload["api_key"],
            base_url=payload["base_url"],
        )

        request_kwargs: dict[str, Any] = {
            "model": payload["model"],
            "messages": [
                {"role": "system", "content": payload["system_prompt"]},
                {"role": "user", "content": payload["user_prompt"]},
            ],
            "max_tokens": payload["max_tokens"],
            "stream": payload["stream"],
        }

        if not payload.get("thinking_enabled", False):
            request_kwargs["temperature"] = payload["temperature"]

        response_format = payload.get("response_format")
        if response_format:
            request_kwargs["response_format"] = {"type": response_format}

        extra_body: dict[str, Any] = {}
        extra_body["thinking"] = {
            "type": "enabled" if payload.get("thinking_enabled", False) else "disabled"
        }
        if extra_body:
            request_kwargs["extra_body"] = extra_body

        reasoning_effort = payload.get("reasoning_effort")
        if reasoning_effort:
            request_kwargs["reasoning_effort"] = reasoning_effort

        response = client.chat.completions.create(**request_kwargs)
        message = response.choices[0].message
        content = message.content or ""
        return {
            "content": content,
            "reasoning_content": getattr(message, "reasoning_content", None),
        }
