"""Tests for CLI report formatting."""

from __future__ import annotations


def make_final_result() -> dict:
    return {
        "input_summary": {
            "snapshot_id": "demo-001",
            "node_count": 3,
            "link_count": 2,
            "path_count": 1,
            "flow_count": 1,
        },
        "global_semantic_state": {
            "status": "abnormal",
            "summary": "The whole network is abnormal because the aggregation segment is overloaded.",
            "key_evidence": [
                {"id": "node-b", "reason": "aggregation node is overloaded"},
                {"id": "flow-1", "reason": "critical flow is impacted"},
            ],
        },
        "semantic_root_cause": {
            "primary_cause": "Primary fault domain is aggregation-node overload at node-b.",
            "secondary_causes": ["Link link-ab degradation is a secondary propagated symptom."],
            "reasoning_summary": "Node overload at the aggregation layer is the dominant cause and drives flow degradation.",
            "key_evidence": [
                {"id": "node-b", "reason": "dominant abnormal object across agents"},
                {"id": "link-ab", "reason": "degradation appears downstream of node-b"},
            ],
        },
        "closed_loop_control": {
            "recommended_action": "Relieve load on node-b and protect flow-1 first.",
            "candidate_actions": [
                "Relieve load on node-b and protect flow-1 first.",
                "Temporarily reroute traffic away from link-ab.",
            ],
            "target_objects": ["node-b", "flow-1", "link-ab"],
            "control_reasoning": "node-b is the best mitigation target and flow-1 has the highest business priority.",
        },
    }


def test_format_report_contains_required_sections_in_order() -> None:
    from semantic_net_cli.reporting.formatter import format_report

    report = format_report(make_final_result())

    input_index = report.index("Input Summary")
    global_index = report.index("Global Semantic State")
    root_index = report.index("Semantic Root-Cause Diagnosis")
    control_index = report.index("Closed-Loop Semantic Control")

    assert input_index < global_index < root_index < control_index
    assert "snapshot_id: demo-001" in report
    assert "status: abnormal" in report
    assert "Primary fault domain is aggregation-node overload at node-b." in report
    assert "Relieve load on node-b and protect flow-1 first." in report


def test_format_report_includes_concrete_evidence_and_targets() -> None:
    from semantic_net_cli.reporting.formatter import format_report

    report = format_report(make_final_result())

    assert "- node-b: aggregation node is overloaded" in report
    assert "- link-ab: degradation appears downstream of node-b" in report
    assert "target_objects: node-b, flow-1, link-ab" in report
