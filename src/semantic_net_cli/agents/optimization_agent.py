"""Optimization Agent: C_k + F_k^mid -> U_k."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.output_parser import parse_agent_json_output
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.facts import IntermediateFactSet
from semantic_net_cli.models.task_outputs import CauseSet, OptimizationAction


class OptimizationAgent:
    """Produce optimization recommendation U_k from causes and facts."""

    name = "optimization_agent"

    def __init__(self, llm_client: Any, settings: AgentLLMSettings) -> None:
        self.llm_client = llm_client
        self.settings = settings

    def run(self, cause_set: CauseSet, fact_set: IntermediateFactSet) -> OptimizationAction:
        context = {
            "C_k": cause_set.model_dump(),
            "F_k^mid": fact_set.model_dump(),
            "do_not_execute": True,
        }
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        payload = parse_agent_json_output(self.name, response)
        return OptimizationAction.model_validate(payload)
