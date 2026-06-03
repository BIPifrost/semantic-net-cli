"""Tests for CLI report formatting."""

from __future__ import annotations

from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction


def make_final_result() -> dict:
    fact = SemanticFact(
        fact_id="performance-1",
        category="performance",
        fact_type="threshold_violation",
        subject_id="c_wifi_ap1",
        summary="c_wifi_ap1 shows degraded wireless performance.",
        evidence=[{"id": "c_wifi_ap1", "reason": "loss_rate and retransmission_rate are elevated"}],
        confidence=0.86,
    )
    return {
        "input_summary": {
            "object_count": 6,
            "node_count": 3,
            "interface_count": 2,
            "channel_count": 1,
        },
        "intermediate_fact_set": IntermediateFactSet.from_agent_outputs({"performance_agent": [fact]}),
        "network_state": NetworkState(
            state_id="S_k",
            status="degraded",
            summary="Wireless access segment is degraded.",
            key_fact_ids=["performance-1"],
            confidence=0.82,
        ),
        "cause_set": CauseSet(
            cause_set_id="C_k",
            primary_cause="Wireless channel degradation on c_wifi_ap1",
            causes=["interference_increase"],
            evidence_fact_ids=["performance-1"],
            confidence=0.8,
        ),
        "optimization_action": OptimizationAction(
            action_id="U_k",
            recommended_action="Reduce load on c_wifi_ap1 and protect video traffic.",
            target_object_ids=["c_wifi_ap1", "sta1"],
            candidate_actions=["adjust wireless channel", "rate-limit low-priority traffic"],
            reasoning="Cause set points to wireless interference.",
            confidence=0.78,
        ),
    }


def test_report_contains_picture_pipeline_sections_in_order() -> None:
    from semantic_net_cli.reporting.formatter import format_report

    report = format_report(make_final_result())

    assert report.index("Input Summary") < report.index("Intermediate Semantic Fact Set")
    assert report.index("Intermediate Semantic Fact Set") < report.index("Current Network State S_k")
    assert report.index("Current Network State S_k") < report.index("Cause Set C_k")
    assert report.index("Cause Set C_k") < report.index("Optimization Action U_k")


def test_report_includes_fact_counts_and_task_output_fields() -> None:
    from semantic_net_cli.reporting.formatter import format_report

    report = format_report(make_final_result())

    assert "object_count: 6" in report
    assert "performance_fact_count: 1" in report
    assert "status: degraded" in report
    assert "primary_cause: Wireless channel degradation on c_wifi_ap1" in report
    assert "target_object_ids: c_wifi_ap1, sta1" in report
