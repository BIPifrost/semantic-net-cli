"""Tests for the routing and forwarding agent."""

from __future__ import annotations

import json

from semantic_net_cli.agents.routing_forwarding import RoutingForwardingAgent
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


def make_snapshot_with_abnormal_path() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-routing-001"},
            "nodes": [
                {
                    "id": "node-1",
                    "type": "router",
                    "role": "core",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.40,
                        "cpu": 0.30,
                        "queue": 0.10,
                    },
                },
                {
                    "id": "node-2",
                    "type": "router",
                    "role": "aggregation",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.44,
                        "cpu": 0.31,
                        "queue": 0.11,
                    },
                },
            ],
            "links": [
                {
                    "id": "link-1",
                    "source": "node-1",
                    "target": "node-2",
                    "type": "wired",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": 8.0,
                        "loss": 0.0,
                        "utilization": 0.55,
                        "cpu": None,
                        "queue": None,
                    },
                }
            ],
            "paths": [
                {
                    "id": "path-bad",
                    "node_ids": ["node-1", "node-2"],
                    "link_ids": ["link-1"],
                    "semantic_state": "abnormal",
                }
            ],
            "flows": [
                {
                    "id": "flow-1",
                    "source": "node-1",
                    "target": "node-2",
                    "path_id": "path-bad",
                    "semantic_state": "abnormal",
                    "importance": "high",
                }
            ],
        }
    )


def test_routing_forwarding_agent_builds_context_and_parses_response() -> None:
    snapshot = make_snapshot_with_abnormal_path()
    captured_payload: dict = {}

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "routing_forwarding",
                    "status": "abnormal",
                    "findings": ["Path path-bad is abnormal"],
                    "evidence": [{"id": "path-bad", "reason": "semantic_state=abnormal"}],
                    "confidence": 0.83,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = RoutingForwardingAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, {})

    assert result.agent == "routing_forwarding"
    assert result.status == "abnormal"
    assert result.evidence[0].id == "path-bad"
    user_prompt = captured_payload["user_prompt"]
    assert "path-bad" in user_prompt
    assert "abnormal_paths" in user_prompt
