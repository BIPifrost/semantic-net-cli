"""Tests for the business flow impact agent."""

from __future__ import annotations

import json

from semantic_net_cli.agents.flow_impact import FlowImpactAgent
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.llm.structured_output import parse_agent_output
from semantic_net_cli.models.agent_output import AgentOutput
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


def make_snapshot_for_flow_impact() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-flow-001"},
            "nodes": [
                {
                    "id": "node-a",
                    "type": "host",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.20,
                        "cpu": 0.18,
                        "queue": 0.02
                    }
                },
                {
                    "id": "node-b",
                    "type": "switch",
                    "role": "aggregation",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.45,
                        "cpu": 0.31,
                        "queue": 0.10
                    }
                },
                {
                    "id": "node-c",
                    "type": "host",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.21,
                        "cpu": 0.19,
                        "queue": 0.03
                    }
                }
            ],
            "links": [
                {
                    "id": "link-ab",
                    "source": "node-a",
                    "target": "node-b",
                    "type": "wired",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": 6.0,
                        "loss": 0.0,
                        "utilization": 0.41,
                        "cpu": None,
                        "queue": None
                    }
                },
                {
                    "id": "link-bc",
                    "source": "node-b",
                    "target": "node-c",
                    "type": "wired",
                    "semantic_state": "degraded",
                    "metrics": {
                        "latency": 20.0,
                        "loss": 0.02,
                        "utilization": 0.88,
                        "cpu": None,
                        "queue": None
                    }
                }
            ],
            "paths": [
                {
                    "id": "path-abc",
                    "node_ids": ["node-a", "node-b", "node-c"],
                    "link_ids": ["link-ab", "link-bc"],
                    "semantic_state": "degraded"
                }
            ],
            "flows": [
                {
                    "id": "flow-abc",
                    "source": "node-a",
                    "target": "node-c",
                    "path_id": "path-abc",
                    "semantic_state": "degraded",
                    "importance": "critical"
                }
            ]
        }
    )


def test_flow_impact_agent_uses_prior_results_to_build_context() -> None:
    snapshot = make_snapshot_for_flow_impact()
    captured_payload: dict = {}

    prior_results = {
        "link_quality": AgentOutput.model_validate(
            {
                "agent": "link_quality",
                "status": "degraded",
                "findings": ["Link link-bc is degraded"],
                "evidence": [{"id": "link-bc", "reason": "semantic_state=degraded"}],
                "confidence": 0.82,
            }
        )
    }

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "flow_impact",
                    "status": "degraded",
                    "findings": ["Flow flow-abc is impacted"],
                    "evidence": [{"id": "flow-abc", "reason": "depends on degraded link-bc"}],
                    "confidence": 0.84,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = FlowImpactAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, prior_results)

    assert result.agent == "flow_impact"
    assert result.status == "degraded"
    assert result.evidence[0].id == "flow-abc"
    user_prompt = captured_payload["user_prompt"]
    assert "predicted_impacted_flows" in user_prompt
    assert "flow-abc" in user_prompt
