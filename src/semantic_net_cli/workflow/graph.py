"""LangGraph workflow assembly for the semantic network analysis pipeline."""

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from semantic_net_cli.agents.closed_loop_control import ClosedLoopControlAgent
from semantic_net_cli.agents.fault_domain import FaultDomainAgent
from semantic_net_cli.agents.flow_impact import FlowImpactAgent
from semantic_net_cli.agents.global_state import GlobalStateAgent
from semantic_net_cli.agents.link_quality import LinkQualityAgent
from semantic_net_cli.agents.node_bottleneck import NodeBottleneckAgent
from semantic_net_cli.agents.routing_forwarding import RoutingForwardingAgent
from semantic_net_cli.agents.topology_dependency import TopologyDependencyAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import LLMConfigLoader
from semantic_net_cli.llm.structured_output import parse_agent_output
from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.workflow.state import WorkflowState


AGENT_ORDER = [
    "topology_dependency",
    "link_quality",
    "routing_forwarding",
    "node_bottleneck",
    "flow_impact",
    "global_state",
    "fault_domain",
    "closed_loop_control",
]


def build_workflow(config_path: str, llm_client: LLMClient | None = None) -> Any:
    """Build and compile the fixed-order LangGraph workflow."""

    loader = LLMConfigLoader(config_path)
    loader.load()
    client = llm_client or LLMClient()
    graph = StateGraph(WorkflowState)

    graph.add_node("prepare", _prepare_initial_state)
    graph.add_node(
        "topology_dependency",
        _make_agent_node(
            TopologyDependencyAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("topology_dependency"),
            )
        ),
    )
    graph.add_node(
        "link_quality",
        _make_agent_node(
            LinkQualityAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("link_quality"),
            )
        ),
    )
    graph.add_node(
        "routing_forwarding",
        _make_agent_node(
            RoutingForwardingAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("routing_forwarding"),
            )
        ),
    )
    graph.add_node(
        "node_bottleneck",
        _make_agent_node(
            NodeBottleneckAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("node_bottleneck"),
            )
        ),
    )
    graph.add_node(
        "flow_impact",
        _make_agent_node(
            FlowImpactAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("flow_impact"),
            )
        ),
    )
    graph.add_node(
        "global_state",
        _make_agent_node(
            GlobalStateAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("global_state"),
            )
        ),
    )
    graph.add_node(
        "fault_domain",
        _make_agent_node(
            FaultDomainAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("fault_domain"),
            )
        ),
    )
    graph.add_node(
        "closed_loop_control",
        _make_agent_node(
            ClosedLoopControlAgent(
                llm_client=client,
                structured_output=parse_agent_output,
                settings=loader.resolve("closed_loop_control"),
            )
        ),
    )
    graph.add_node("finalize", _finalize_state)

    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "topology_dependency")
    graph.add_edge("topology_dependency", "link_quality")
    graph.add_edge("link_quality", "routing_forwarding")
    graph.add_edge("routing_forwarding", "node_bottleneck")
    graph.add_edge("node_bottleneck", "flow_impact")
    graph.add_edge("flow_impact", "global_state")
    graph.add_edge("global_state", "fault_domain")
    graph.add_edge("fault_domain", "closed_loop_control")
    graph.add_edge("closed_loop_control", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def _prepare_initial_state(state: WorkflowState) -> dict[str, Any]:
    """Prepare shared workflow state before agent execution."""

    snapshot = state["snapshot"]
    return {
        "agent_results": {},
        "input_summary": {
            "snapshot_id": snapshot.metadata.snapshot_id,
            "node_count": len(snapshot.nodes),
            "link_count": len(snapshot.links),
            "path_count": len(snapshot.paths),
            "flow_count": len(snapshot.flows),
        },
        "global_semantic_state": {
            "status": "unknown",
            "summary": "",
            "key_evidence": [],
        },
        "semantic_root_cause": {
            "primary_cause": "",
            "secondary_causes": [],
            "reasoning_summary": "",
            "key_evidence": [],
        },
        "closed_loop_control": {
            "recommended_action": "",
            "candidate_actions": [],
            "target_objects": [],
            "control_reasoning": "",
        },
        "config_path": state.get("config_path", ""),
        "resolved_agent_settings": state.get("resolved_agent_settings", {}),
    }


def _make_agent_node(agent: Any) -> Callable[[WorkflowState], dict[str, Any]]:
    """Wrap one agent into a LangGraph node function."""

    def node(state: WorkflowState) -> dict[str, Any]:
        prior_results = dict(state.get("agent_results", {}))
        result = agent.run(state["snapshot"], prior_results)
        updated_results = {**prior_results, agent.name: result}
        return {"agent_results": updated_results}

    return node


def _finalize_state(state: WorkflowState) -> dict[str, Any]:
    """Assemble the final workflow-level outputs."""

    agent_results: dict[str, AgentOutput] = state.get("agent_results", {})

    global_result = agent_results.get("global_state", AgentOutput.unknown("global_state"))
    fault_result = agent_results.get("fault_domain", AgentOutput.unknown("fault_domain"))
    control_result = agent_results.get(
        "closed_loop_control", AgentOutput.unknown("closed_loop_control")
    )

    return {
        "global_semantic_state": {
            "status": global_result.status,
            "summary": global_result.findings[0] if global_result.findings else "",
            "key_evidence": [item.model_dump() for item in global_result.evidence],
        },
        "semantic_root_cause": {
            "primary_cause": fault_result.findings[0] if fault_result.findings else "",
            "secondary_causes": fault_result.findings[1:],
            "reasoning_summary": " ".join(fault_result.findings),
            "key_evidence": [item.model_dump() for item in fault_result.evidence],
        },
        "closed_loop_control": {
            "recommended_action": control_result.findings[0] if control_result.findings else "",
            "candidate_actions": control_result.findings,
            "target_objects": [item.id for item in control_result.evidence],
            "control_reasoning": " ".join(item.reason for item in control_result.evidence),
        },
    }
