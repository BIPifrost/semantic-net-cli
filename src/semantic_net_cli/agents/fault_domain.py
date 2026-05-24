"""Fault-domain diagnosis agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class FaultDomainAgent(WorkflowAgent):
    """Diagnose the dominant fault domain from prior agent outputs."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="fault_domain",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run root-cause diagnosis over prior agent outputs."""

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
        object_votes: dict[str, dict[str, Any]] = {}

        for agent_name, result in prior_results.items():
            for item in result.evidence:
                if item.id not in object_votes:
                    object_votes[item.id] = {
                        "id": item.id,
                        "supporting_agents": [],
                        "reasons": [],
                        "statuses": [],
                    }

                object_votes[item.id]["supporting_agents"].append(agent_name)
                object_votes[item.id]["reasons"].append(item.reason)
                object_votes[item.id]["statuses"].append(result.status)

        ranked_objects = sorted(
            object_votes.values(),
            key=lambda item: (
                len(item["supporting_agents"]),
                sum(1 for status in item["statuses"] if status in {"degraded", "congested", "abnormal"}),
            ),
            reverse=True,
        )

        dominant_fault_domain = "unknown"
        if ranked_objects:
            top_id = ranked_objects[0]["id"]
            node_ids = {node.id for node in snapshot.nodes}
            link_ids = {link.id for link in snapshot.links}
            path_ids = {path.id for path in snapshot.paths}
            flow_ids = {flow.id for flow in snapshot.flows}

            if top_id in node_ids:
                dominant_fault_domain = "node"
            elif top_id in link_ids:
                dominant_fault_domain = "link"
            elif top_id in path_ids:
                dominant_fault_domain = "path"
            elif top_id in flow_ids:
                dominant_fault_domain = "flow"

        abnormal_results = {
            agent_name: result.model_dump()
            for agent_name, result in prior_results.items()
            if result.status in {"degraded", "congested", "abnormal"}
        }

        status_set = {result.status for result in prior_results.values()}

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "input_summary": {
                "node_count": len(snapshot.nodes),
                "link_count": len(snapshot.links),
                "path_count": len(snapshot.paths),
                "flow_count": len(snapshot.flows),
            },
            "summary": {
                "dominant_fault_domain": dominant_fault_domain,
                "top_ranked_object_ids": [item["id"] for item in ranked_objects[:5]],
                "mixed_signal": len(status_set) > 1,
                "abnormal_agent_count": len(abnormal_results),
            },
            "ranked_evidence_objects": ranked_objects,
            "abnormal_prior_results": abnormal_results,
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
