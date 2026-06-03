"""Analysis Agent: S_k + F_k^mid -> C_k."""

from __future__ import annotations

import json
from typing import Any

from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.facts import IntermediateFactSet
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState


class AnalysisAgent:
    """Produce cause set C_k from current state and intermediate facts."""

    name = "analysis_agent"

    def __init__(self, llm_client: Any, settings: AgentLLMSettings) -> None:
        self.llm_client = llm_client
        self.settings = settings

    def run(self, network_state: NetworkState, fact_set: IntermediateFactSet) -> CauseSet:
        context = {"S_k": network_state.model_dump(), "F_k^mid": fact_set.model_dump()}
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        payload = json.loads(response["content"])
        return CauseSet.model_validate(payload)
