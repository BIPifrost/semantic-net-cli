from semantic_net_cli.control.executor import SimulatedControlExecutor
from semantic_net_cli.models.task_outputs import OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {
                        "status": "degraded",
                        "metrics": {"loss_rate": 0.014, "utilization": 0.76},
                    },
                    "relations": {"connects": ["ap1_wlan0", "sta1_wlan0"]},
                    "actions": [],
                }
            ]
        }
    )


def test_simulated_executor_turns_u_k_into_execution_record() -> None:
    action = OptimizationAction(
        action_id="U_k",
        recommended_action="Adjust wireless channel.",
        target_object_ids=["c_wifi_ap1"],
        candidate_actions=["adjust wireless channel", "protect video traffic"],
        reasoning="Interference detected.",
        confidence=0.78,
    )

    record = SimulatedControlExecutor().execute(action, make_graph())

    assert record.execution_id == "exec-U_k"
    assert record.source_action_id == "U_k"
    assert record.status == "succeeded"
    assert record.target_object_ids == ["c_wifi_ap1"]
    assert record.applied_actions == ["adjust wireless channel", "protect video traffic"]
    assert "c_wifi_ap1" in record.feedback_summary


def test_simulated_executor_skips_when_action_has_no_targets() -> None:
    action = OptimizationAction(
        action_id="U_k",
        recommended_action="No safe target.",
        target_object_ids=[],
        candidate_actions=[],
        reasoning="No target object was identified.",
        confidence=0.2,
    )

    record = SimulatedControlExecutor().execute(action, make_graph())

    assert record.status == "skipped"
    assert record.applied_actions == ["No safe target."]


def test_simulated_executor_marks_damped_status_when_requested() -> None:
    action = OptimizationAction(
        action_id="U_k",
        recommended_action="Adjust wireless channel.",
        target_object_ids=["c_wifi_ap1"],
        candidate_actions=["adjust wireless channel"],
        reasoning="Interference detected.",
        confidence=0.78,
    )

    record = SimulatedControlExecutor().execute(action, make_graph(), mode="damped")

    assert record.status == "damped"
