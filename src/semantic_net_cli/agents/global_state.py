"""Global semantic state agent for semantic network analysis."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.agents.base import WorkflowAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.prompts import build_system_prompt, build_user_prompt
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class GlobalStateAgent(WorkflowAgent):
    """Summarize prior agent results into one global semantic-state judgment."""

    def __init__(
        self,
        llm_client: Any,
        structured_output: Any,
        settings: AgentLLMSettings,
    ) -> None:
        super().__init__(
            name="global_state",
            llm_client=llm_client,
            structured_output=structured_output,
        )
        self.settings = settings

    def run(
        self,
        snapshot: SemanticSnapshot,
        prior_results: dict[str, AgentOutput],
    ) -> AgentOutput:
        """Run global semantic-state summarization over prior agent outputs."""

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
        severity_order = {
            "unknown": 0,
            "normal": 1,
            "degraded": 2,
            "congested": 3,
            "abnormal": 4,
        }

        strongest_status = "unknown"
        consolidated_evidence = []
        agent_summaries = []

        for agent_name, result in prior_results.items():
            if severity_order.get(result.status, 0) > severity_order.get(strongest_status, 0):
                strongest_status = result.status

            summary = {
                "agent": agent_name,
                "status": result.status,
                "findings": result.findings,
                "evidence_ids": [item.id for item in result.evidence],
                "confidence": result.confidence,
            }
            agent_summaries.append(summary)

            for item in result.evidence:
                consolidated_evidence.append(
                    {
                        "source_agent": agent_name,
                        "id": item.id,
                        "reason": item.reason,
                    }
                )

        return {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "input_summary": {
                "node_count": len(snapshot.nodes),
                "link_count": len(snapshot.links),
                "path_count": len(snapshot.paths),
                "flow_count": len(snapshot.flows),
            },
            "agent_summaries": agent_summaries,
            "summary": {
                "participating_agents": sorted(prior_results.keys()),
                "strongest_status": strongest_status,
                "abnormal_agent_count": sum(
                    1 for result in prior_results.values() if result.status in {"degraded", "congested", "abnormal"}
                ),
            },
            "consolidated_evidence": consolidated_evidence,
            "prior_results": {key: value.model_dump() for key, value in prior_results.items()},
        }
