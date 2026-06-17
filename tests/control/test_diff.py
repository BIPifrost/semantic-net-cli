from semantic_net_cli.control.diff import build_topology_change_set
from semantic_net_cli.models.twin import SemanticTwinGraph, TwinAction


def test_build_topology_change_set_reports_added_actions_and_attribute_changes() -> None:
    before = SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {"status": "degraded"},
                    "relations": {},
                    "actions": [],
                }
            ]
        }
    )
    after = SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {
                        "status": "degraded",
                        "control_feedback": {"last_execution_id": "exec-U_k"},
                    },
                    "relations": {},
                    "actions": [
                        TwinAction(
                            action_id="exec-U_k",
                            action_type="control_execution",
                            status="succeeded",
                            reason="adjust wireless channel",
                            result="accepted",
                        ).model_dump()
                    ],
                }
            ]
        }
    )

    change_set = build_topology_change_set(before, after)

    assert change_set["changed_object_count"] == 1
    assert change_set["changes"][0]["object_id"] == "c_wifi_ap1"
    assert change_set["changes"][0]["added_action_ids"] == ["exec-U_k"]
    assert "control_feedback" in change_set["changes"][0]["changed_attributes"]
