"""Shared agent interface for the semantic network analysis pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.models.agent_output import AgentOutput
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
