"""Shared workflow state for the semantic twin two-layer pipeline."""

from __future__ import annotations

from typing import Any, TypedDict

from semantic_net_cli.models.control import ControlExecutionRecord
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph


class WorkflowState(TypedDict, total=False):
    """Shared state passed through the LangGraph workflow."""

    twin_graph: SemanticTwinGraph
    history_context: dict[str, Any]
    front_layer_outputs: dict[str, list[SemanticFact]]
    intermediate_fact_set: IntermediateFactSet
    network_state: NetworkState
    cause_set: CauseSet
    optimization_action: OptimizationAction
    control_execution: ControlExecutionRecord
    updated_twin_graph: SemanticTwinGraph
    next_history_context: dict[str, Any]
    input_summary: dict[str, Any]
