"""Link quality agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class LinkQualityAgent(WorkflowAgent):
    """Analyze link-level semantic degradation and congestion."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="link_quality",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run link quality analysis over all links in the snapshot."""

        context = self._build_context(snapshot, prior_results)
        response = self.llm_client.invoke(
            agent_name=self.name,
            settings=self.settings,
            system_prompt=build_system_prompt(self.name),
            user_prompt=build_user_prompt(self.name, context),
        )
        return self.structured_output(self.name, response)

    def _build_context(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> dict[str, Any]:
        degraded_links = []
        congested_links = []
        abnormal_links = []

        links = []
        for link in snapshot.links:
            record = {
                "id": link.id,
                "source": link.source,
                "target": link.target,
                "semantic_state": link.semantic_state,
                "metrics": link.metrics.model_dump(),
            }
            links.append(record)

            if link.semantic_state == "degraded":
                degraded_links.append(link.id)
            elif link.semantic_state == "congested":
                congested_links.append(link.id)
            elif link.semantic_state == "abnormal":
                abnormal_links.append(link.id)

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "links": links,
            "summary": {
                "total_links": len(snapshot.links),
                "degraded_links": degraded_links,
                "congested_links": congested_links,
                "abnormal_links": abnormal_links,
            },
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
