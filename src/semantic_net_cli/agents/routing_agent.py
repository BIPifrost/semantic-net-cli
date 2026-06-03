"""Routing perspective agent for F_k^mid extraction."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import parse_fact_response
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.facts import SemanticFact
from semantic_net_cli.models.twin import SemanticTwinGraph


class RoutingAgent:
    """Extract routing facts from routes_to relation semantics."""

    name = "routing_agent"

    def __init__(self, llm_client: Any, settings: AgentLLMSettings) -> None:
        self.llm_client = llm_client
        self.settings = settings

    def run(self, graph: SemanticTwinGraph) -> list[SemanticFact]:
        context = {
            "G_k": [item.model_dump() for item in graph.objects],
            "focus": ["routing policy", "path change", "path availability"],
            "required_outputs": ["route switch", "path anomaly", "unreachable route or path"],
        }
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        return parse_fact_response(response)
