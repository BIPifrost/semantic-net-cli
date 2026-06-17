"""Run the closed-loop workflow for a fixed number of iterations."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.control.diff import build_topology_change_set
from semantic_net_cli.control.feedback import build_history_context_from_twin_graph
from semantic_net_cli.models.twin import SemanticTwinGraph
from semantic_net_cli.reporting.formatter import format_report
from semantic_net_cli.reporting.result_logger import ResultLogger


def run_control_loop(
    *,
    workflow: Any,
    initial_graph: SemanticTwinGraph,
    max_iterations: int,
    logger: ResultLogger,
) -> dict[str, Any]:
    """Run exactly max_iterations closed-loop workflow iterations."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

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
            }
        )
        current_graph = result["updated_twin_graph"]
        history_context = result["next_history_context"]

    summary = {
        "iteration_count": max_iterations,
        "iteration_summaries": iteration_summaries,
    }
    logger.write_run_summary(run_dir=run_dir, summary=summary, final_graph=current_graph)
    return {
        "run_dir": run_dir,
        "iteration_count": max_iterations,
        "iteration_summaries": iteration_summaries,
        "final_graph": current_graph,
    }
