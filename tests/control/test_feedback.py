from semantic_net_cli.control.feedback import (
    apply_control_feedback_to_twin_graph,
    build_history_context_from_twin_graph,
)
from semantic_net_cli.models.control import (
    ControlExecutionRecord,
    MetricObservation,
    MetricUpdate,
    PropagatedControlEffect,
)
from semantic_net_cli.models.twin import SemanticTwinGraph


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {"status": "degraded", "metrics": {"loss_rate": 0.014}},
                    "relations": {"connects": ["ap1_wlan0", "sta1_wlan0"]},
                    "actions": [],
                },
                {
                    "id": "sta1",
                    "type": "node:wireless_terminal",
                    "attributes": {"status": "active"},
                    "relations": {},
                    "actions": [],
                },
            ]
        }
    )


def make_record() -> ControlExecutionRecord:
    return ControlExecutionRecord(
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
                after=0.0112,
                unit="ratio",
            )
        ],
        confidence=0.78,
    )


def test_apply_feedback_appends_control_action_to_target_object() -> None:
    updated = apply_control_feedback_to_twin_graph(make_graph(), make_record())

    target = updated.by_id["c_wifi_ap1"]

    assert len(target.actions) == 1
    assert target.actions[0].action_id == "exec-U_k"
    assert target.actions[0].action_type == "control_execution"
    assert target.actions[0].status == "succeeded"
    assert target.actions[0].reason == "adjust wireless channel"
    assert target.actions[0].result == "Simulated execution accepted for c_wifi_ap1."
    assert target.attributes["control_feedback"]["last_execution_id"] == "exec-U_k"


def test_apply_feedback_does_not_mutate_original_graph() -> None:
    graph = make_graph()

    updated = apply_control_feedback_to_twin_graph(graph, make_record())

    assert graph.by_id["c_wifi_ap1"].actions == []
    assert updated.by_id["c_wifi_ap1"].actions != []


def test_build_history_context_collects_action_records() -> None:
    updated = apply_control_feedback_to_twin_graph(make_graph(), make_record())

    context = build_history_context_from_twin_graph(updated)

    assert context["action_count"] == 1
    assert context["recent_actions"][0]["action_id"] == "exec-U_k"
    assert context["recent_actions"][0]["object_id"] == "c_wifi_ap1"


def test_apply_feedback_writes_propagated_metric_updates() -> None:
    graph = make_graph()
    effect = PropagatedControlEffect(
        effect_id="effect-exec-U_k",
        source_execution_id="exec-U_k",
        mode="normal",
        changed_object_ids=["c_wifi_ap1"],
        metric_updates=[
            MetricUpdate(
                object_id="c_wifi_ap1",
                metric_name="loss_rate",
                before=0.014,
                after=0.01148,
                reason="direct action effect",
            )
        ],
        propagation_summary="Applied normal propagation.",
    )

    updated = apply_control_feedback_to_twin_graph(graph, make_record(), effect)

    target = updated.by_id["c_wifi_ap1"]
    assert target.attributes["metrics"]["loss_rate"] == 0.01148
    assert target.attributes["control_feedback"]["propagation_mode"] == "normal"
    assert target.attributes["control_feedback"]["effect_id"] == "effect-exec-U_k"
