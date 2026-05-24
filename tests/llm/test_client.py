"""Tests for the shared LLM client wrapper."""

from __future__ import annotations

from types import SimpleNamespace

from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import AgentLLMSettings


def make_settings() -> AgentLLMSettings:
    return AgentLLMSettings(
        provider="deepseek",
        api_format="openai",
        model="deepseek-v4-flash",
        api_key="placeholder-key",
        base_url="https://api.deepseek.com",
        temperature=0.2,
        max_tokens=1200,
        thinking_enabled=False,
        reasoning_effort=None,
        stream=False,
        response_format="json_object",
    )


def test_llm_client_forwards_payload_to_transport() -> None:
    captured: dict = {}

    def transport(payload: dict) -> dict:
        captured.update(payload)
        return {"content": "{\"status\":\"normal\"}"}

    client = LLMClient(transport=transport)
    response = client.invoke(
        agent_name="link_quality",
        settings=make_settings(),
        system_prompt="system",
        user_prompt="user",
    )

    assert captured["agent_name"] == "link_quality"
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["api_format"] == "openai"
    assert captured["system_prompt"] == "system"
    assert captured["user_prompt"] == "user"
    assert response["content"] == "{\"status\":\"normal\"}"


def test_llm_client_default_transport_uses_openai_compatible_request(monkeypatch) -> None:
    captured: dict = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"agent":"x","status":"normal","findings":[],"evidence":[],"confidence":1.0}',
                            reasoning_content=None,
                        )
                    )
                ]
            )

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, *, api_key: str, base_url: str) -> None:
            captured["client_api_key"] = api_key
            captured["client_base_url"] = base_url
            self.chat = FakeChat()

    monkeypatch.setattr("semantic_net_cli.llm.client.OpenAI", FakeOpenAI)

    client = LLMClient()
    response = client.invoke(
        agent_name="link_quality",
        settings=make_settings(),
        system_prompt="system",
        user_prompt="user",
    )

    assert captured["client_api_key"] == "placeholder-key"
    assert captured["client_base_url"] == "https://api.deepseek.com"
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1]["role"] == "user"
    assert response["content"].startswith("{")


def test_llm_client_default_transport_rejects_unsupported_api_format() -> None:
    client = LLMClient()
    settings = make_settings().model_copy(update={"api_format": "anthropic"})

    try:
        client.invoke(
            agent_name="link_quality",
            settings=settings,
            system_prompt="system",
            user_prompt="user",
        )
    except RuntimeError as exc:
        assert "Unsupported live api_format" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when no live transport is configured")
