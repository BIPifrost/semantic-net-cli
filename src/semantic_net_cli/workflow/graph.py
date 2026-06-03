"""LangGraph workflow assembly for the semantic twin two-layer pipeline."""

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from semantic_net_cli.agents.analysis_agent import AnalysisAgent
from semantic_net_cli.agents.node_semantic_agent import NodeSemanticAgent
from semantic_net_cli.agents.optimization_agent import OptimizationAgent
from semantic_net_cli.agents.performance_agent import PerformanceAgent
from semantic_net_cli.agents.routing_agent import RoutingAgent
from semantic_net_cli.agents.topology_agent import TopologyAgent
from semantic_net_cli.agents.traffic_agent import TrafficAgent
from semantic_net_cli.agents.understanding_agent import UnderstandingAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import LLMConfigLoader
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.workflow.state import WorkflowState


AGENT_ORDER = [
    "topology_agent",
    "routing_agent",
    "traffic_agent",
    "performance_agent",
    "node_semantic_agent",
    "aggregate_facts",
    "understanding_agent",
    "analysis_agent",
    "optimization_agent",
]


def build_workflow(config_path: str, llm_client: LLMClient | None = None) -> Any:
    """Build and compile the fixed-order two-layer LangGraph workflow."""

    loader = LLMConfigLoader(config_path)
    loader.load()
    client = llm_client or LLMClient()
    graph = StateGraph(WorkflowState)

    graph.add_node("prepare", _prepare_initial_state)
    graph.add_node(
        "topology_agent",
        _make_front_layer_agent_node(
            TopologyAgent(llm_client=client, settings=loader.resolve("topology_agent"))
        ),
    )
    graph.add_node(
        "routing_agent",
        _make_front_layer_agent_node(
            RoutingAgent(llm_client=client, settings=loader.resolve("routing_agent"))
        ),
    )
    graph.add_node(
        "traffic_agent",
        _make_front_layer_agent_node(
            TrafficAgent(llm_client=client, settings=loader.resolve("traffic_agent"))
        ),
    )
    graph.add_node(
        "performance_agent",
        _make_front_layer_agent_node(
            PerformanceAgent(llm_client=client, settings=loader.resolve("performance_agent"))
        ),
    )
    graph.add_node(
        "node_semantic_agent",
        _make_front_layer_agent_node(
            NodeSemanticAgent(llm_client=client, settings=loader.resolve("node_semantic_agent"))
        ),
    )
    graph.add_node("aggregate_facts", _aggregate_facts)
    graph.add_node(
        "understanding_agent",
        _make_understanding_node(
            UnderstandingAgent(llm_client=client, settings=loader.resolve("understanding_agent"))
        ),
    )
    graph.add_node(
        "analysis_agent",
        _make_analysis_node(
            AnalysisAgent(llm_client=client, settings=loader.resolve("analysis_agent"))
        ),
    )
    graph.add_node(
        "optimization_agent",
        _make_optimization_node(
            OptimizationAgent(llm_client=client, settings=loader.resolve("optimization_agent"))
        ),
    )
    graph.add_node("finalize", _finalize_state)

    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "topology_agent")
    graph.add_edge("topology_agent", "routing_agent")
    graph.add_edge("routing_agent", "traffic_agent")
    graph.add_edge("traffic_agent", "performance_agent")
    graph.add_edge("performance_agent", "node_semantic_agent")
    graph.add_edge("node_semantic_agent", "aggregate_facts")
    graph.add_edge("aggregate_facts", "understanding_agent")
    graph.add_edge("understanding_agent", "analysis_agent")
    graph.add_edge("analysis_agent", "optimization_agent")
    graph.add_edge("optimization_agent", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def _prepare_initial_state(state: WorkflowState) -> dict[str, Any]:
    """Prepare shared workflow state before agent execution."""

    twin_graph = state["twin_graph"]
    return {
        "front_layer_outputs": {},
        "history_context": state.get("history_context", {}),
        "input_summary": {
            "object_count": len(twin_graph.objects),
            "node_count": len(twin_graph.objects_by_base_type("node")),
            "interface_count": len(twin_graph.objects_by_base_type("interface")),
            "channel_count": len(twin_graph.objects_by_base_type("channel")),
        },
    }


def _make_front_layer_agent_node(agent: Any) -> Callable[[WorkflowState], dict[str, Any]]:
    """Wrap a perspective fact agent into a LangGraph node function."""

    def node(state: WorkflowState) -> dict[str, Any]:
        outputs: dict[str, list[SemanticFact]] = dict(state.get("front_layer_outputs", {}))
        outputs[agent.name] = agent.run(state["twin_graph"])
        return {"front_layer_outputs": outputs}

    return node


def _aggregate_facts(state: WorkflowState) -> dict[str, Any]:
    """Aggregate perspective facts into F_k^mid."""

    return {
        "intermediate_fact_set": IntermediateFactSet.from_agent_outputs(
            state["front_layer_outputs"]
        )
    }


def _make_understanding_node(agent: UnderstandingAgent) -> Callable[[WorkflowState], dict[str, Any]]:
    def node(state: WorkflowState) -> dict[str, Any]:
        return {
            "network_state": agent.run(
                state["intermediate_fact_set"],
                state.get("history_context", {}),
            )
        }

    return node


def _make_analysis_node(agent: AnalysisAgent) -> Callable[[WorkflowState], dict[str, Any]]:
    def node(state: WorkflowState) -> dict[str, Any]:
        return {
            "cause_set": agent.run(
                state["network_state"],
                state["intermediate_fact_set"],
            )
        }

    return node


def _make_optimization_node(agent: OptimizationAgent) -> Callable[[WorkflowState], dict[str, Any]]:
    def node(state: WorkflowState) -> dict[str, Any]:
        return {
            "optimization_action": agent.run(
                state["cause_set"],
                state["intermediate_fact_set"],
            )
        }

    return node


def _finalize_state(state: WorkflowState) -> dict[str, Any]:
    """Return no extra data; state already contains terminal outputs."""

    return {}
