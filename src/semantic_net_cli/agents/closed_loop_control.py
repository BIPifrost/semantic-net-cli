"""Closed-loop semantic control agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class ClosedLoopControlAgent(WorkflowAgent):
    """Recommend closed-loop control actions from diagnosis outputs."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="closed_loop_control",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run recommendation-level control analysis over prior diagnosis results."""

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
        target_object_ids: list[str] = []
        protected_flow_ids: list[str] = []

        for result in prior_results.values():
            for item in result.evidence:
                if item.id not in target_object_ids:
                    target_object_ids.append(item.id)

        for flow in snapshot.flows:
            if flow.importance in {"high", "critical"}:
                protected_flow_ids.append(flow.id)

        fault_domain_result = prior_results.get("fault_domain")
        global_state_result = prior_results.get("global_state")

        recommended_action_hint = "observe"
        if fault_domain_result is not None:
            joined_findings = " ".join(fault_domain_result.findings).lower()
            if "node" in joined_findings or any(
                item.id in {node.id for node in snapshot.nodes} for item in fault_domain_result.evidence
            ):
                recommended_action_hint = "rebalance_or_relieve_node_load"
            elif "link" in joined_findings or any(
                item.id in {link.id for link in snapshot.links} for item in fault_domain_result.evidence
            ):
                recommended_action_hint = "reroute_or_reduce_link_pressure"
            elif "path" in joined_findings:
                recommended_action_hint = "adjust_forwarding_path"

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "input_summary": {
                "node_count": len(snapshot.nodes),
                "link_count": len(snapshot.links),
                "path_count": len(snapshot.paths),
                "flow_count": len(snapshot.flows),
            },
            "summary": {
                "recommended_action_hint": recommended_action_hint,
                "target_object_ids": target_object_ids,
                "protected_flow_ids": protected_flow_ids,
                "do_not_execute": True,
            },
            "global_state_result": (
                global_state_result.model_dump() if global_state_result is not None else None
            ),
            "fault_domain_result": (
                fault_domain_result.model_dump() if fault_domain_result is not None else None
            ),
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
