from semantic_net_cli.control.effects import ControlEffectPropagator
from semantic_net_cli.models.control import ControlExecutionRecord
from semantic_net_cli.models.twin import SemanticTwinGraph


def make_wireless_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {
                        "status": "degraded",
                        "metrics": {
                            "loss_rate": 0.014,
                            "retransmission_rate": 0.10,
                            "avg_snr_db": 20,
                            "throughput_mbps": 110,
                            "delay_ms": 14.2,
                            "utilization": 0.76,
                        },
                    },
                    "relations": {"connects": ["ap1_wlan0", "sta1_wlan0"]},
                    "actions": [],
                },
                {
                    "id": "sta1_wlan0",
                    "type": "interface:wireless",
                    "attributes": {
                        "metrics": {
                            "error_packets": 15,
                            "rssi_dbm": -71,
                            "snr_db": 15,
                        }
                    },
                    "relations": {"connected_by": ["c_wifi_ap1"]},
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
        feedback_summary="accepted",
        confidence=0.8,
    )


def test_wireless_channel_adjustment_updates_coupled_metrics_and_related_interface() -> None:
    effect = ControlEffectPropagator().propagate(
        graph=make_wireless_graph(),
        record=make_record(),
        mode="normal",
        damping_factor=1.0,
    )

    updates = {(item.object_id, item.metric_name): item for item in effect.metric_updates}

    assert updates[("c_wifi_ap1", "loss_rate")].after < 0.014
    assert updates[("c_wifi_ap1", "retransmission_rate")].after < 0.10
    assert updates[("c_wifi_ap1", "throughput_mbps")].after > 110
    assert updates[("c_wifi_ap1", "delay_ms")].after < 14.2
    assert updates[("sta1_wlan0", "snr_db")].after > 15
    assert effect.changed_object_ids == ["c_wifi_ap1", "sta1_wlan0"]


def test_damped_mode_reduces_update_magnitude() -> None:
    normal = ControlEffectPropagator().propagate(
        graph=make_wireless_graph(),
        record=make_record(),
        mode="normal",
        damping_factor=1.0,
    )
    damped = ControlEffectPropagator().propagate(
        graph=make_wireless_graph(),
        record=make_record(),
        mode="damped",
        damping_factor=0.5,
    )

    normal_loss = next(item for item in normal.metric_updates if item.metric_name == "loss_rate")
    damped_loss = next(item for item in damped.metric_updates if item.metric_name == "loss_rate")

    assert damped.mode == "damped"
    assert damped_loss.after > normal_loss.after
