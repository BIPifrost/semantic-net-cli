from pydantic import ValidationError

from semantic_net_cli.models.control import ControlExecutionRecord, MetricObservation


def test_control_execution_record_matches_closed_loop_contract() -> None:
    record = ControlExecutionRecord(
        execution_id="exec-U_k",
        source_action_id="U_k",
        executor="simulated_control_executor",
        status="succeeded",
        target_object_ids=["c_wifi_ap1"],
        applied_actions=["adjust wireless channel"],
        feedback_summary="Simulated execution accepted for c_wifi_ap1.",
        metric_observations=[
            MetricObservation(
                object_id="c_wifi_ap1",
                metric_name="loss_rate",
                before=0.014,
                after=0.009,
                unit="ratio",
            )
        ],
        confidence=0.76,
    )

    assert record.execution_id == "exec-U_k"
    assert record.status == "succeeded"
    assert record.metric_observations[0].after == 0.009


def test_control_execution_record_rejects_unknown_status() -> None:
    try:
        ControlExecutionRecord(
            execution_id="exec-U_k",
            source_action_id="U_k",
            executor="simulated_control_executor",
            status="maybe",
            target_object_ids=["c_wifi_ap1"],
            applied_actions=["adjust wireless channel"],
            feedback_summary="bad status",
            confidence=0.5,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected invalid execution status to be rejected")
