"""Routing and forwarding agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class RoutingForwardingAgent(WorkflowAgent):
    """Analyze path-level abnormal routing and forwarding behavior."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="routing_forwarding",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run routing and forwarding analysis over path objects."""

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
        node_ids = {node.id for node in snapshot.nodes}
        link_ids = {link.id for link in snapshot.links}

        abnormal_paths = []
        path_records = []

        for path in snapshot.paths:
            missing_nodes = [node_id for node_id in path.node_ids if node_id not in node_ids]
            missing_links = [link_id for link_id in path.link_ids if link_id not in link_ids]
            record = {
                "id": path.id,
                "node_ids": path.node_ids,
                "link_ids": path.link_ids,
                "semantic_state": path.semantic_state,
                "missing_nodes": missing_nodes,
                "missing_links": missing_links,
                "hop_count": len(path.node_ids),
            }
            path_records.append(record)

            if path.semantic_state in {"degraded", "congested", "abnormal"}:
                abnormal_paths.append(path.id)
            elif missing_nodes or missing_links:
                abnormal_paths.append(path.id)

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "paths": path_records,
            "summary": {
                "total_paths": len(snapshot.paths),
                "abnormal_paths": abnormal_paths,
            },
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
