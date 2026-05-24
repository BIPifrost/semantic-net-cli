"""Tests for the node bottleneck agent."""

from __future__ import annotations

import json

from semantic_net_cli.agents.node_bottleneck import NodeBottleneckAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.structured_output import parse_agent_output
from semantic_net_cli.models.schema import SemanticSnapshot


def make_settings() -> AgentLLMSettings:
    return AgentLLMSettings(
        provider="openai",
        model="gpt-4.1-mini",
        api_key="placeholder-key",
        base_url="https://api.openai.com/v1",
        temperature=0.2,
        max_tokens=1200,
    )


def make_snapshot_with_bottleneck_node() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-node-001"},
            "nodes": [
                {
                    "id": "node-ok",
                    "type": "switch",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.32,
                        "cpu": 0.24,
                        "queue": 0.08,
                    },
                },
                {
                    "id": "node-hot",
                    "type": "router",
                    "role": "core",
                    "semantic_state": "abnormal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.92,
                        "cpu": 0.95,
                        "queue": 0.84,
                    },
                },
            ],
            "links": [
                {
                    "id": "link-1",
                    "source": "node-ok",
                    "target": "node-hot",
                    "type": "wired",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": 8.0,
                        "loss": 0.0,
                        "utilization": 0.50,
                        "cpu": None,
                        "queue": None,
                    },
                }
            ],
            "paths": [
                {
                    "id": "path-1",
                    "node_ids": ["node-ok", "node-hot"],
                    "link_ids": ["link-1"],
                    "semantic_state": "degraded",
                }
            ],
            "flows": [
                {
                    "id": "flow-1",
                    "source": "node-ok",
                    "target": "node-hot",
                    "path_id": "path-1",
                    "semantic_state": "degraded",
                    "importance": "high",
                }
            ],
        }
    )


def test_node_bottleneck_agent_builds_context_and_parses_response() -> None:
    snapshot = make_snapshot_with_bottleneck_node()
    captured_payload: dict = {}

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "node_bottleneck",
                    "status": "abnormal",
                    "findings": ["Node node-hot is a bottleneck"],
                    "evidence": [{"id": "node-hot", "reason": "cpu/utilization/queue high"}],
                    "confidence": 0.89,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = NodeBottleneckAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, {})

    assert result.agent == "node_bottleneck"
    assert result.status == "abnormal"
    assert result.evidence[0].id == "node-hot"
    user_prompt = captured_payload["user_prompt"]
    assert "node-hot" in user_prompt
    assert "bottleneck_nodes" in user_prompt
