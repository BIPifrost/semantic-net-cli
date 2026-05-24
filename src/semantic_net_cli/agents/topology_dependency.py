"""Topology dependency agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class TopologyDependencyAgent(WorkflowAgent):
    """Analyze dependencies across nodes, links, paths, and flows."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="topology_dependency",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run topology dependency analysis over the full snapshot."""

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
        path_ids = {path.id for path in snapshot.paths}

        flow_dependencies = []
        missing_references = []

        for flow in snapshot.flows:
            flow_record = {
                "flow_id": flow.id,
                "path_id": flow.path_id,
                "path_exists": flow.path_id in path_ids,
            }
            flow_dependencies.append(flow_record)
            if flow.path_id not in path_ids:
                missing_references.append(
                    {
                        "kind": "flow_to_path",
                        "source_id": flow.id,
                        "missing_id": flow.path_id,
                    }
                )

        path_dependencies = []
        for path in snapshot.paths:
            missing_nodes = [node_id for node_id in path.node_ids if node_id not in node_ids]
            missing_links = [link_id for link_id in path.link_ids if link_id not in link_ids]
            path_dependencies.append(
                {
                    "path_id": path.id,
                    "node_ids": path.node_ids,
                    "link_ids": path.link_ids,
                    "missing_nodes": missing_nodes,
                    "missing_links": missing_links,
                }
            )
            for node_id in missing_nodes:
                missing_references.append(
                    {
                        "kind": "path_to_node",
                        "source_id": path.id,
                        "missing_id": node_id,
                    }
                )
            for link_id in missing_links:
                missing_references.append(
                    {
                        "kind": "path_to_link",
                        "source_id": path.id,
                        "missing_id": link_id,
                    }
                )

        link_dependencies = [
            {
                "link_id": link.id,
                "source": link.source,
                "target": link.target,
                "source_exists": link.source in node_ids,
                "target_exists": link.target in node_ids,
            }
            for link in snapshot.links
        ]
        for link in snapshot.links:
            if link.source not in node_ids:
                missing_references.append(
                    {
                        "kind": "link_to_source_node",
                        "source_id": link.id,
                        "missing_id": link.source,
                    }
                )
            if link.target not in node_ids:
                missing_references.append(
                    {
                        "kind": "link_to_target_node",
                        "source_id": link.id,
                        "missing_id": link.target,
                    }
                )

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "nodes": [node.model_dump() for node in snapshot.nodes],
            "links": [link.model_dump() for link in snapshot.links],
            "paths": [path.model_dump() for path in snapshot.paths],
            "flows": [flow.model_dump() for flow in snapshot.flows],
            "flow_dependencies": flow_dependencies,
            "path_dependencies": path_dependencies,
            "link_dependencies": link_dependencies,
            "missing_references": missing_references,
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
