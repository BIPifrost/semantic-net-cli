"""Run the closed-loop workflow for a fixed number of iterations."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.control.diff import build_topology_change_set
from semantic_net_cli.control.effects import ControlEffectPropagator
from semantic_net_cli.control.feedback import (
    apply_control_feedback_to_twin_graph,
    build_history_context_from_twin_graph,
)
from semantic_net_cli.control.stability import StabilityMonitor
from semantic_net_cli.models.twin import SemanticTwinGraph
from semantic_net_cli.reporting.formatter import format_report
from semantic_net_cli.reporting.result_logger import ResultLogger


def run_control_loop(
    *,
    workflow: Any,
    initial_graph: SemanticTwinGraph,
    max_iterations: int,
    logger: ResultLogger,
    stability_monitor: StabilityMonitor | None = None,
    effect_propagator: ControlEffectPropagator | None = None,
) -> dict[str, Any]:
    """Run closed-loop workflow iterations until convergence or max_iterations."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

    monitor = stability_monitor or StabilityMonitor()
    propagator = effect_propagator or ControlEffectPropagator()
    terminal_reason = "max_iterations_reached"
    run_dir = logger.start_run()
    current_graph = initial_graph
    history_context = build_history_context_from_twin_graph(current_graph)
    iteration_summaries: list[dict[str, Any]] = []

    for iteration_index in range(1, max_iterations + 1):
        result = workflow.invoke(
            {
                "twin_graph": current_graph,
                "history_context": history_context,
            }
        )
        preliminary_changes = build_topology_change_set(current_graph, result["updated_twin_graph"])
        assessment = monitor.assess(
            iteration=iteration_index,
            network_status=result["network_state"].status,
            primary_cause=result["cause_set"].primary_cause,
            recommended_action=result["optimization_action"].recommended_action,
            target_object_ids=result["optimization_action"].target_object_ids,
            changed_object_count=preliminary_changes["changed_object_count"],
        )
        mode = "damped" if assessment.stability == "damped" else "normal"
        if mode == "damped" and result["control_execution"].status == "succeeded":
            result["control_execution"] = result["control_execution"].model_copy(
                update={"status": "damped"}
            )
        effect = propagator.propagate(
            graph=current_graph,
            record=result["control_execution"],
            mode=mode,
            damping_factor=assessment.damping_factor,
        )
        updated_graph = apply_control_feedback_to_twin_graph(
            current_graph,
            result["control_execution"],
            effect,
        )
        result["propagated_effect"] = effect
        result["updated_twin_graph"] = updated_graph
        result["next_history_context"] = build_history_context_from_twin_graph(updated_graph)
        result["stability_assessment"] = assessment
        topology_changes = build_topology_change_set(current_graph, result["updated_twin_graph"])
        report_text = format_report(result)
        logger.write_iteration(
            run_dir=run_dir,
            iteration_index=iteration_index,
            input_graph=current_graph,
            result=result,
            topology_changes=topology_changes,
            report_text=report_text,
        )
        iteration_summaries.append(
            {
                "iteration": iteration_index,
                "network_status": result["network_state"].status,
                "primary_cause": result["cause_set"].primary_cause,
                "recommended_action": result["optimization_action"].recommended_action,
                "execution_status": result["control_execution"].status,
                "changed_object_count": topology_changes["changed_object_count"],
                "stability": assessment.stability,
                "damping_factor": assessment.damping_factor,
            }
        )
        current_graph = result["updated_twin_graph"]
        history_context = result["next_history_context"]
        if assessment.should_stop:
            terminal_reason = assessment.terminal_reason or assessment.stability
            break

    summary = {
        "iteration_count": len(iteration_summaries),
        "iteration_summaries": iteration_summaries,
        "terminal_reason": terminal_reason,
    }
    logger.write_run_summary(run_dir=run_dir, summary=summary, final_graph=current_graph)
    return {
        "run_dir": run_dir,
        "iteration_count": len(iteration_summaries),
        "iteration_summaries": iteration_summaries,
        "terminal_reason": terminal_reason,
        "final_graph": current_graph,
    }
