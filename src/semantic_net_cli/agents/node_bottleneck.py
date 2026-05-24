"""Node bottleneck agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class NodeBottleneckAgent(WorkflowAgent):
    """Analyze node-level bottleneck conditions."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="node_bottleneck",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run node bottleneck analysis over all nodes in the snapshot."""

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
        bottleneck_nodes = []
        abnormal_nodes = []
        node_records = []

        for node in snapshot.nodes:
            metrics = node.metrics.model_dump()
            record = {
                "id": node.id,
                "type": node.type,
                "role": node.role,
                "semantic_state": node.semantic_state,
                "metrics": metrics,
            }
            node_records.append(record)

            if node.semantic_state in {"degraded", "congested", "abnormal"}:
                abnormal_nodes.append(node.id)

            cpu = metrics.get("cpu")
            utilization = metrics.get("utilization")
            queue = metrics.get("queue")
            if (
                node.semantic_state in {"degraded", "congested", "abnormal"}
                or (cpu is not None and cpu >= 0.85)
                or (utilization is not None and utilization >= 0.85)
                or (queue is not None and queue >= 0.80)
            ):
                bottleneck_nodes.append(node.id)

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "nodes": node_records,
            "summary": {
                "total_nodes": len(snapshot.nodes),
                "abnormal_nodes": abnormal_nodes,
                "bottleneck_nodes": bottleneck_nodes,
            },
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
