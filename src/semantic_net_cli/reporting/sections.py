"""Section builders for the CLI report formatter."""

from __future__ import annotations

from typing import Any


def build_input_summary_section(final_result: dict) -> str:
    """Build the Input Summary section."""

    summary = final_result["input_summary"]
    lines = [
        "Input Summary",
        f"object_count: {summary['object_count']}",
        f"node_count: {summary['node_count']}",
        f"interface_count: {summary['interface_count']}",
        f"channel_count: {summary['channel_count']}",
    ]
    return "\n".join(lines)


def build_intermediate_fact_set_section(final_result: dict) -> str:
    """Build the Intermediate Semantic Fact Set section."""

    fact_set = final_result["intermediate_fact_set"]
    lines = [
        "Intermediate Semantic Fact Set",
        f"fact_set_id: {fact_set.fact_set_id}",
        f"topology_fact_count: {len(fact_set.topology_facts)}",
        f"routing_fact_count: {len(fact_set.routing_facts)}",
        f"traffic_fact_count: {len(fact_set.traffic_facts)}",
        f"performance_fact_count: {len(fact_set.performance_facts)}",
        f"node_semantic_fact_count: {len(fact_set.node_semantic_facts)}",
        "facts:",
    ]
    if not fact_set.all_facts:
        lines.append("- none")
    for fact in fact_set.all_facts:
        lines.append(
            f"- {fact.fact_id} [{fact.category}/{fact.fact_type}] {fact.subject_id}: {fact.summary}"
        )
    return "\n".join(lines)


def build_network_state_section(final_result: dict) -> str:
    """Build the Current Network State S_k section."""

    state = final_result["network_state"]
    lines = [
        "Current Network State S_k",
        f"state_id: {state.state_id}",
        f"status: {state.status}",
        f"summary: {state.summary}",
        f"key_fact_ids: {_join_or_none(state.key_fact_ids)}",
        f"confidence: {state.confidence}",
    ]
    return "\n".join(lines)


def build_cause_set_section(final_result: dict) -> str:
    """Build the Cause Set C_k section."""

    cause_set = final_result["cause_set"]
    lines = [
        "Cause Set C_k",
        f"cause_set_id: {cause_set.cause_set_id}",
        f"primary_cause: {cause_set.primary_cause}",
        f"causes: {_join_or_none(cause_set.causes)}",
        f"evidence_fact_ids: {_join_or_none(cause_set.evidence_fact_ids)}",
        f"confidence: {cause_set.confidence}",
    ]
    return "\n".join(lines)


def build_optimization_action_section(final_result: dict) -> str:
    """Build the Optimization Action U_k section."""

    action = final_result["optimization_action"]
    lines = [
        "Optimization Action U_k",
        f"action_id: {action.action_id}",
        f"recommended_action: {action.recommended_action}",
        f"target_object_ids: {_join_or_none(action.target_object_ids)}",
        f"candidate_actions: {_join_or_none(action.candidate_actions, separator=' | ')}",
        f"reasoning: {action.reasoning}",
        f"confidence: {action.confidence}",
    ]
    return "\n".join(lines)


def _join_or_none(items: list[Any], separator: str = ", ") -> str:
    if not items:
        return "none"
    return separator.join(str(item) for item in items)
