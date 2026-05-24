"""CLI report formatter for semantic network analysis results."""

from __future__ import annotations

from semantic_net_cli.reporting.sections import (
    build_closed_loop_control_section,
    build_global_state_section,
    build_input_summary_section,
    build_root_cause_section,
)


def format_report(final_result: dict) -> str:
    """Format the final workflow result into a terminal-readable report."""

    sections = [
        build_input_summary_section(final_result),
        build_global_state_section(final_result),
        build_root_cause_section(final_result),
        build_closed_loop_control_section(final_result),
    ]
    return "\n\n".join(sections)
