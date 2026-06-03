"""Shared agent interface for the semantic network analysis pipeline."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.facts import SemanticFact
from semantic_net_cli.models.schema import SemanticSnapshot


class BaseAgent(ABC):
    """Base class for all LLM-backed semantic-network agents."""

    def __init__(self, name: str, llm_client: LLMClient, structured_output: Any) -> None:
        self.name = name
        self.llm_client = llm_client
        self.structured_output = structured_output

    @abstractmethod
    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run the agent against the shared snapshot and prior results."""


class WorkflowAgent(BaseAgent):
    """Concrete shared base for agents implemented later in the pipeline."""

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        raise NotImplementedError("Concrete agents must implement run().")


def parse_fact_response(raw_response: Any) -> list[SemanticFact]:
    """Parse a front-layer LLM response into semantic facts."""

    content = (
        raw_response["content"]
        if isinstance(raw_response, dict) and "content" in raw_response
        else raw_response
    )
    payload = json.loads(content) if isinstance(content, str) else content
    return [SemanticFact.model_validate(item) for item in payload.get("facts", [])]
