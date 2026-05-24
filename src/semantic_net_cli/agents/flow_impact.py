"""Business flow impact agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class FlowImpactAgent(WorkflowAgent):
    """Analyze which business flows are impacted by upstream abnormalities."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="flow_impact",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run business-flow impact analysis using prior bottom-layer results."""

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
        path_by_id = {path.id: path for path in snapshot.paths}
        impacted_flow_ids = set()

        for result in prior_results.values():
            for item in result.evidence:
                for flow in snapshot.flows:
                    path = path_by_id.get(flow.path_id)
                    if path is None:
                        continue
                    if item.id == flow.path_id:
                        impacted_flow_ids.add(flow.id)
                    if item.id in path.link_ids:
                        impacted_flow_ids.add(flow.id)
                    if item.id in path.node_ids:
                        impacted_flow_ids.add(flow.id)

        flows = []
        for flow in snapshot.flows:
            path = path_by_id.get(flow.path_id)
            flows.append(
                {
                    "id": flow.id,
                    "source": flow.source,
                    "target": flow.target,
                    "path_id": flow.path_id,
                    "semantic_state": flow.semantic_state,
                    "importance": flow.importance,
                    "path_node_ids": path.node_ids if path else [],
                    "path_link_ids": path.link_ids if path else [],
                    "predicted_impacted": flow.id in impacted_flow_ids,
                }
            )

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "flows": flows,
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
            "summary": {
                "total_flows": len(snapshot.flows),
                "predicted_impacted_flows": sorted(impacted_flow_ids),
            },
        }
