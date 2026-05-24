"""Tests for the fixed semantic-network snapshot schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from semantic_net_cli.models.schema import SemanticSnapshot


def make_valid_snapshot() -> dict:
    return {
        "metadata": {
            "snapshot_id": "snapshot-001",
        },
        "nodes": [
            {
                "id": "node-1",
                "type": "router",
                "role": "core",
                "semantic_state": "normal",
                "metrics": {
                    "latency": None,
                    "loss": None,
                    "utilization": 0.45,
                    "cpu": 0.33,
                    "queue": 0.10,
                },
            }
        ],
        "links": [
            {
                "id": "link-1",
                "source": "node-1",
                "target": "node-2",
                "type": "wired",
                "semantic_state": "degraded",
                "metrics": {
                    "latency": 10.0,
                    "loss": 0.02,
                    "utilization": 0.77,
                    "cpu": None,
                    "queue": None,
                },
            }
        ],
        "paths": [
            {
                "id": "path-1",
                "node_ids": ["node-1", "node-2"],
                "link_ids": ["link-1"],
                "semantic_state": "normal",
            }
        ],
        "flows": [
            {
                "id": "flow-1",
                "source": "node-1",
                "target": "node-2",
                "path_id": "path-1",
                "semantic_state": "normal",
                "importance": "high",
            }
        ],
    }


def test_semantic_snapshot_accepts_valid_minimal_payload() -> None:
    snapshot = SemanticSnapshot.model_validate(make_valid_snapshot())

    assert snapshot.metadata.snapshot_id == "snapshot-001"
    assert len(snapshot.nodes) == 1
    assert len(snapshot.links) == 1
    assert len(snapshot.paths) == 1
    assert len(snapshot.flows) == 1


def test_semantic_snapshot_rejects_missing_top_level_key() -> None:
    payload = make_valid_snapshot()
    payload.pop("flows")

    with pytest.raises(ValidationError):
        SemanticSnapshot.model_validate(payload)


def test_semantic_snapshot_rejects_unsupported_enum_value() -> None:
    payload = make_valid_snapshot()
    payload["nodes"][0]["type"] = "server"

    with pytest.raises(ValidationError):
        SemanticSnapshot.model_validate(payload)
