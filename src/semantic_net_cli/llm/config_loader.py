"""Load unified LLM configuration for all agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AgentLLMSettings(BaseModel):
    """Resolved LLM settings for one agent."""

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    api_format: str = Field(default="openai", min_length=1)
    temperature: float
    max_tokens: int
    thinking_enabled: bool = False
    reasoning_effort: str | None = None
    stream: bool = False
    response_format: str = Field(default="json_object", min_length=1)


class LLMConfig(BaseModel):
    """Top-level LLM configuration file model."""

    global_: AgentLLMSettings = Field(alias="global")
    agents: dict[str, dict[str, Any]]


class LLMConfigLoader:
    """Load and resolve global plus per-agent LLM settings."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._config: LLMConfig | None = None

    def load(self) -> LLMConfig:
        """Load and cache the configuration file."""

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self._config = LLMConfig.model_validate(data)
        return self._config

    def resolve(self, agent_name: str) -> AgentLLMSettings:
        """Resolve effective settings for one agent."""

        if self._config is None:
            self.load()

        assert self._config is not None
        base = self._config.global_.model_dump()
        overrides = self._config.agents.get(agent_name, {})
        merged = {**base, **overrides}
        return AgentLLMSettings.model_validate(merged)
