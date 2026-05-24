"""Tests for the topology dependency agent."""

from __future__ import annotations

import json

from semantic_net_cli.agents.topology_dependency import TopologyDependencyAgent
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


def make_snapshot_with_broken_flow_reference() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-topology-001"},
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
                        "utilization": 0.42,
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
                    "id": "path-1",
                    "node_ids": ["node-1", "node-2"],
                    "link_ids": ["link-1"],
                    "semantic_state": "normal",
                }
            ],
            "flows": [
                {
                    "id": "flow-bad",
                    "source": "node-1",
                    "target": "node-2",
                    "path_id": "missing-path",
                    "semantic_state": "abnormal",
                    "importance": "high",
                }
            ],
        }
    )


def test_topology_dependency_agent_builds_context_and_parses_response() -> None:
    snapshot = make_snapshot_with_broken_flow_reference()
    captured_payload: dict = {}

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "topology_dependency",
                    "status": "degraded",
                    "findings": ["Flow flow-bad references a missing path"],
                    "evidence": [{"id": "flow-bad", "reason": "missing-path"}],
                    "confidence": 0.88,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = TopologyDependencyAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, {})

    assert result.agent == "topology_dependency"
    assert result.status == "degraded"
    assert result.evidence[0].id == "flow-bad"
    user_prompt = captured_payload["user_prompt"]
    assert "missing-path" in user_prompt
    assert "flow_dependencies" in user_prompt
