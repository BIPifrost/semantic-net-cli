"""Understanding Agent: F_k^mid + history_context -> S_k."""

from __future__ import annotations

import json
from typing import Any

from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.facts import IntermediateFactSet
from semantic_net_cli.models.task_outputs import NetworkState


class UnderstandingAgent:
    """Produce current network state S_k from intermediate facts."""

    name = "understanding_agent"

    def __init__(self, llm_client: Any, settings: AgentLLMSettings) -> None:
        self.llm_client = llm_client
        self.settings = settings

    def run(self, fact_set: IntermediateFactSet, history_context: dict[str, Any]) -> NetworkState:
        context = {"F_k^mid": fact_set.model_dump(), "history_context": history_context}
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        payload = json.loads(response["content"])
        return NetworkState.model_validate(payload)
