"""Topology perspective agent for F_k^mid extraction."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.llm.output_parser import parse_agent_json_output
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.facts import SemanticFact
from semantic_net_cli.models.twin import SemanticTwinGraph


class TopologyAgent:
    """Extract topology facts from connectivity and relation structure."""

    name = "topology_agent"

    def __init__(self, llm_client: Any, settings: AgentLLMSettings) -> None:
        self.llm_client = llm_client
        self.settings = settings

    def run(self, graph: SemanticTwinGraph) -> list[SemanticFact]:
        context = {
            "G_k": [item.model_dump() for item in graph.objects],
            "focus": ["connectivity", "topology change", "key links"],
            "required_outputs": [
                "topology change",
                "cut or bottleneck object",
                "disconnected region",
            ],
        }
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        payload = parse_agent_json_output(self.name, response)
        return [SemanticFact.model_validate(item) for item in payload.get("facts", [])]
