from pydantic import ValidationError

from semantic_net_cli.models.control import (
    ControlExecutionRecord,
    MetricObservation,
    PropagatedControlEffect,
    StabilityAssessment,
)


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


def test_propagated_control_effect_records_metric_updates_and_mode() -> None:
    effect = PropagatedControlEffect(
        effect_id="effect-exec-U_k",
        source_execution_id="exec-U_k",
        mode="normal",
        changed_object_ids=["c_wifi_ap1", "sta1_wlan0"],
        metric_updates=[
            {
                "object_id": "c_wifi_ap1",
                "metric_name": "loss_rate",
                "before": 0.014,
                "after": 0.01148,
                "reason": "adjust wireless channel reduces loss",
            }
        ],
        propagation_summary="Applied wireless channel adjustment with normal damping.",
    )

    assert effect.mode == "normal"
    assert effect.changed_object_ids == ["c_wifi_ap1", "sta1_wlan0"]
    assert effect.metric_updates[0].metric_name == "loss_rate"


def test_stability_assessment_supports_damped_and_terminal_reason() -> None:
    assessment = StabilityAssessment(
        iteration=4,
        stability="damped",
        terminal_reason=None,
        should_stop=False,
        damping_factor=0.5,
        oscillation_count=1,
        signature="degraded|wireless_A|shift_to_B|c_wifi_ap1",
        rationale="A-B-A pattern detected; entering damped mode.",
    )

    assert assessment.stability == "damped"
    assert assessment.damping_factor == 0.5
    assert assessment.should_stop is False
