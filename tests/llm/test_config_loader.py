"""Tests for unified LLM config loading and per-agent resolution."""

from __future__ import annotations

from pathlib import Path

from semantic_net_cli.llm.config_loader import LLMConfigLoader


def test_config_loader_reads_global_defaults() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "llm_config.example.json"
    loader = LLMConfigLoader(path)
    settings = loader.resolve("topology_agent")

    assert settings.provider == "your_provider"
    assert settings.api_format == "openai"
    assert settings.model == "your_model_name"
    assert settings.api_key == "your_api_key"
    assert settings.base_url == "https://your-llm-endpoint.example.com"
    assert settings.temperature == 0.2
    assert settings.thinking_enabled is False
    assert settings.reasoning_effort is None
    assert settings.stream is False
    assert settings.response_format == "json_object"


def test_config_loader_applies_agent_overrides() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "llm_config.example.json"
    loader = LLMConfigLoader(path)
    settings = loader.resolve("performance_agent")

    assert settings.model == "your_model_name"
    assert settings.temperature == 0.2
    assert settings.max_tokens == 10000
    assert settings.api_format == "openai"
