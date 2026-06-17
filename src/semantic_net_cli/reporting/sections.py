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


def build_control_execution_section(final_result: dict) -> str:
    """Build the Control Action Execution section."""

    execution = final_result["control_execution"]
    lines = [
        "Control Action Execution",
        f"execution_id: {execution.execution_id}",
        f"source_action_id: {execution.source_action_id}",
        f"executor: {execution.executor}",
        f"execution_status: {execution.status}",
        f"target_object_ids: {_join_or_none(execution.target_object_ids)}",
        f"applied_actions: {_join_or_none(execution.applied_actions, separator=' | ')}",
        f"feedback_summary: {execution.feedback_summary}",
        f"confidence: {execution.confidence}",
    ]
    return "\n".join(lines)


def build_effect_propagation_section(final_result: dict) -> str:
    """Build the Control Effect Propagation section."""

    effect = final_result.get("propagated_effect")
    if effect is None:
        return "Control Effect Propagation\nnone"
    return "\n".join(
        [
            "Control Effect Propagation",
            f"effect_id: {effect.effect_id}",
            f"source_execution_id: {effect.source_execution_id}",
            f"propagation_mode: {effect.mode}",
            f"changed_object_ids: {_join_or_none(effect.changed_object_ids)}",
            f"metric_update_count: {len(effect.metric_updates)}",
            f"propagation_summary: {effect.propagation_summary}",
        ]
    )


def build_stability_assessment_section(final_result: dict) -> str:
    """Build the Loop Stability Assessment section."""

    assessment = final_result.get("stability_assessment")
    if assessment is None:
        return "Loop Stability Assessment\nnone"
    return "\n".join(
        [
            "Loop Stability Assessment",
            f"iteration: {assessment.iteration}",
            f"stability: {assessment.stability}",
            f"terminal_reason: {assessment.terminal_reason or 'none'}",
            f"should_stop: {assessment.should_stop}",
            f"damping_factor: {assessment.damping_factor}",
            f"oscillation_count: {assessment.oscillation_count}",
            f"signature: {assessment.signature}",
            f"rationale: {assessment.rationale}",
        ]
    )


def build_feedback_section(final_result: dict) -> str:
    """Build the Feedback To Semantic Twin G_k+1 section."""

    updated_graph = final_result["updated_twin_graph"]
    next_history_context = final_result["next_history_context"]
    lines = [
        "Feedback To Semantic Twin G_k+1",
        f"updated_object_count: {len(updated_graph.objects)}",
        f"next_history_action_count: {next_history_context.get('action_count', 0)}",
        "feedback_targets:",
    ]
    execution = final_result["control_execution"]
    if not execution.target_object_ids:
        lines.append("- none")
    for target_id in execution.target_object_ids:
        lines.append(f"- {target_id}")
    return "\n".join(lines)


def _join_or_none(items: list[Any], separator: str = ", ") -> str:
    if not items:
        return "none"
    return separator.join(str(item) for item in items)
