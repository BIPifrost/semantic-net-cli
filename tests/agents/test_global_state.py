"""Tests for the global semantic state agent."""

from __future__ import annotations

import json

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


def make_snapshot_for_global_state() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-global-001"},
            "nodes": [
                {
                    "id": "node-a",
                    "type": "host",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.22,
                        "cpu": 0.18,
                        "queue": 0.03,
                    },
                },
                {
                    "id": "node-b",
                    "type": "switch",
                    "role": "aggregation",
                    "semantic_state": "congested",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.89,
                        "cpu": 0.76,
                        "queue": 0.81,
                    },
                },
            ],
            "links": [
                {
                    "id": "link-ab",
                    "source": "node-a",
                    "target": "node-b",
                    "type": "wired",
                    "semantic_state": "degraded",
                    "metrics": {
                        "latency": 18.0,
                        "loss": 0.01,
                        "utilization": 0.87,
                        "cpu": None,
                        "queue": None,
                    },
                }
            ],
            "paths": [
                {
                    "id": "path-ab",
                    "node_ids": ["node-a", "node-b"],
                    "link_ids": ["link-ab"],
                    "semantic_state": "degraded",
                }
            ],
            "flows": [
                {
                    "id": "flow-ab",
                    "source": "node-a",
                    "target": "node-b",
                    "path_id": "path-ab",
                    "semantic_state": "degraded",
                    "importance": "critical",
                }
            ],
        }
    )


def test_global_state_agent_uses_prior_results_for_network_summary() -> None:
    from semantic_net_cli.agents.global_state import GlobalStateAgent

    snapshot = make_snapshot_for_global_state()
    captured_payload: dict = {}

    prior_results = {
        "link_quality": AgentOutput.model_validate(
            {
                "agent": "link_quality",
                "status": "degraded",
                "findings": ["Link link-ab is degraded"],
                "evidence": [{"id": "link-ab", "reason": "latency/loss/utilization elevated"}],
                "confidence": 0.84,
            }
        ),
        "node_bottleneck": AgentOutput.model_validate(
            {
                "agent": "node_bottleneck",
                "status": "abnormal",
                "findings": ["Node node-b is congested and near bottleneck"],
                "evidence": [{"id": "node-b", "reason": "utilization and queue are high"}],
                "confidence": 0.87,
            }
        ),
        "flow_impact": AgentOutput.model_validate(
            {
                "agent": "flow_impact",
                "status": "degraded",
                "findings": ["Flow flow-ab is impacted"],
                "evidence": [{"id": "flow-ab", "reason": "depends on degraded link-ab"}],
                "confidence": 0.86,
            }
        ),
    }

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "global_state",
                    "status": "abnormal",
                    "findings": ["The whole network is abnormal due to coupled link and node degradation"],
                    "evidence": [
                        {"id": "node-b", "reason": "aggregation node congested"},
                        {"id": "link-ab", "reason": "upstream link degraded"},
                        {"id": "flow-ab", "reason": "critical flow impacted"},
                    ],
                    "confidence": 0.88,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = GlobalStateAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, prior_results)

    assert result.agent == "global_state"
    assert result.status == "abnormal"
    assert result.evidence[0].id == "node-b"
    user_prompt = captured_payload["user_prompt"]
    assert "strongest_status" in user_prompt
    assert "abnormal" in user_prompt
    assert "node-b" in user_prompt
    assert "flow-ab" in user_prompt
