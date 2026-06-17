from semantic_net_cli.io.jsonl_loader import load_twin_graph_jsonl
from semantic_net_cli.io.jsonl_writer import write_twin_graph_jsonl
from semantic_net_cli.models.twin import SemanticTwinGraph, TwinAction


def test_write_twin_graph_jsonl_round_trips_updated_actions(tmp_path) -> None:
    graph = SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {"status": "degraded"},
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
    output_path = tmp_path / "updated.jsonl"

    write_twin_graph_jsonl(graph, output_path)
    loaded = load_twin_graph_jsonl(output_path)

    assert loaded.by_id["c_wifi_ap1"].actions[0].action_id == "exec-U_k"
    assert output_path.read_text(encoding="utf-8").count("\n") == 1
