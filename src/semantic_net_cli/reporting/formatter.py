"""CLI report formatter for semantic twin two-layer analysis results."""

from __future__ import annotations

from semantic_net_cli.reporting.sections import (
    build_cause_set_section,
    build_control_execution_section,
    build_effect_propagation_section,
    build_feedback_section,
    build_input_summary_section,
    build_intermediate_fact_set_section,
    build_network_state_section,
    build_optimization_action_section,
    build_stability_assessment_section,
)


def format_report(final_result: dict) -> str:
    """Format the final workflow result into a terminal-readable report."""

    sections = [
        build_input_summary_section(final_result),
        build_intermediate_fact_set_section(final_result),
        build_network_state_section(final_result),
        build_cause_set_section(final_result),
        build_optimization_action_section(final_result),
        build_control_execution_section(final_result),
        build_effect_propagation_section(final_result),
        build_stability_assessment_section(final_result),
        build_feedback_section(final_result),
    ]
    return "\n\n".join(sections)
