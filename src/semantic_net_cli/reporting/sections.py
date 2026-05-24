"""Section builders for the CLI report formatter."""

from __future__ import annotations


def build_input_summary_section(final_result: dict) -> str:
    """Build the Input Summary section."""

    summary = final_result["input_summary"]
    lines = [
        "Input Summary",
        f"snapshot_id: {summary['snapshot_id']}",
        f"node_count: {summary['node_count']}",
        f"link_count: {summary['link_count']}",
        f"path_count: {summary['path_count']}",
        f"flow_count: {summary['flow_count']}",
    ]
    return "\n".join(lines)


def build_global_state_section(final_result: dict) -> str:
    """Build the Global Semantic State section."""

    section = final_result["global_semantic_state"]
    lines = [
        "Global Semantic State",
        f"status: {section['status']}",
        f"summary: {section['summary']}",
        "key_evidence:",
    ]
    lines.extend(_format_evidence(section.get("key_evidence", [])))
    return "\n".join(lines)


def build_root_cause_section(final_result: dict) -> str:
    """Build the Semantic Root-Cause Diagnosis section."""

    section = final_result["semantic_root_cause"]
    secondary = section.get("secondary_causes", [])
    lines = [
        "Semantic Root-Cause Diagnosis",
        f"primary_cause: {section['primary_cause']}",
        f"secondary_causes: {', '.join(secondary) if secondary else 'none'}",
        f"reasoning_summary: {section['reasoning_summary']}",
        "key_evidence:",
    ]
    lines.extend(_format_evidence(section.get("key_evidence", [])))
    return "\n".join(lines)


def build_closed_loop_control_section(final_result: dict) -> str:
    """Build the Closed-Loop Semantic Control section."""

    section = final_result["closed_loop_control"]
    candidate_actions = section.get("candidate_actions", [])
    lines = [
        "Closed-Loop Semantic Control",
        f"recommended_action: {section['recommended_action']}",
        f"candidate_actions: {' | '.join(candidate_actions) if candidate_actions else 'none'}",
        f"target_objects: {', '.join(section.get('target_objects', [])) if section.get('target_objects') else 'none'}",
        f"control_reasoning: {section['control_reasoning']}",
    ]
    return "\n".join(lines)


def _format_evidence(evidence: list[dict]) -> list[str]:
    """Format key evidence lines for terminal output."""

    if not evidence:
        return ["- none"]
    return [f"- {item['id']}: {item['reason']}" for item in evidence]
