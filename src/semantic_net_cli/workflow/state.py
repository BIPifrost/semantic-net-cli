"""Shared workflow state for the semantic network analysis pipeline."""

from __future__ import annotations

from typing import Any, TypedDict

from semantic_net_cli.models.agent_output import AgentOutput
from semantic_net_cli.models.schema import SemanticSnapshot


class InputSummary(TypedDict):
    """Summary of one input snapshot."""

    snapshot_id: str
    node_count: int
    link_count: int
    path_count: int
    flow_count: int


class GlobalSemanticState(TypedDict):
    """Final global semantic-state output."""

    status: str
    summary: str
    key_evidence: list[dict[str, Any]]


class SemanticRootCause(TypedDict):
    """Final semantic root-cause output."""

    primary_cause: str
    secondary_causes: list[str]
    reasoning_summary: str
    key_evidence: list[dict[str, Any]]


class ClosedLoopControl(TypedDict):
    """Final closed-loop semantic control output."""

    recommended_action: str
    candidate_actions: list[str]
    target_objects: list[str]
    control_reasoning: str


class WorkflowState(TypedDict):
    """Shared state passed through the LangGraph workflow."""

    snapshot: SemanticSnapshot
    agent_results: dict[str, AgentOutput]
    input_summary: InputSummary
    global_semantic_state: GlobalSemanticState
    semantic_root_cause: SemanticRootCause
    closed_loop_control: ClosedLoopControl
    config_path: str
    resolved_agent_settings: dict[str, dict[str, Any]]
