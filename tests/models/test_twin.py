from pydantic import ValidationError

from semantic_net_cli.models.twin import SemanticTwinGraph, SemanticTwinObject


def test_twin_object_accepts_node_interface_channel_types() -> None:
    node = SemanticTwinObject.model_validate(
        {"id": "r1", "type": "node:router", "attributes": {}, "relations": {}, "actions": []}
    )
    interface = SemanticTwinObject.model_validate(
        {"id": "r1_eth0", "type": "interface:wired", "attributes": {}, "relations": {}, "actions": []}
    )
    channel = SemanticTwinObject.model_validate(
        {"id": "c1", "type": "channel:wired", "attributes": {}, "relations": {}, "actions": []}
    )

    assert node.base_type == "node"
    assert interface.base_type == "interface"
    assert channel.base_type == "channel"


def test_twin_object_rejects_path_route_transmission_event_types() -> None:
    for invalid_type in ["path:logical", "route:static", "transmission:flow", "event:alarm"]:
        try:
            SemanticTwinObject.model_validate(
                {"id": "bad", "type": invalid_type, "attributes": {}, "relations": {}, "actions": []}
            )
        except ValidationError:
            pass
        else:
            raise AssertionError(f"Expected ValidationError for {invalid_type}")


def test_twin_graph_rejects_duplicate_ids() -> None:
    obj = {"id": "r1", "type": "node:router", "attributes": {}, "relations": {}, "actions": []}

    try:
        SemanticTwinGraph.model_validate({"objects": [obj, obj]})
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected duplicate IDs to be rejected")
