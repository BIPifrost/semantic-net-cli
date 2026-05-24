"""Tests for the link quality agent."""

from __future__ import annotations

import json

from semantic_net_cli.agents.link_quality import LinkQualityAgent
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


def make_snapshot_with_degraded_link() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-link-001"},
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
                        "utilization": 0.45,
                        "cpu": 0.32,
                        "queue": 0.11,
                    },
                },
            ],
            "links": [
                {
                    "id": "link-normal",
                    "source": "node-1",
                    "target": "node-2",
                    "type": "wired",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": 8.0,
                        "loss": 0.0,
                        "utilization": 0.50,
                        "cpu": None,
                        "queue": None,
                    },
                },
                {
                    "id": "link-bad",
                    "source": "node-2",
                    "target": "node-1",
                    "type": "wired",
                    "semantic_state": "degraded",
                    "metrics": {
                        "latency": 26.0,
                        "loss": 0.03,
                        "utilization": 0.91,
                        "cpu": None,
                        "queue": None,
                    },
                },
            ],
            "paths": [
                {
                    "id": "path-1",
                    "node_ids": ["node-1", "node-2"],
                    "link_ids": ["link-normal"],
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
    )


def test_link_quality_agent_builds_context_and_parses_response() -> None:
    snapshot = make_snapshot_with_degraded_link()
    captured_payload: dict = {}

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "link_quality",
                    "status": "degraded",
                    "findings": ["Link link-bad is degraded"],
                    "evidence": [{"id": "link-bad", "reason": "semantic_state=degraded"}],
                    "confidence": 0.81,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = LinkQualityAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, {})

    assert result.agent == "link_quality"
    assert result.status == "degraded"
    assert result.evidence[0].id == "link-bad"
    user_prompt = captured_payload["user_prompt"]
    assert "link-bad" in user_prompt
    assert "degraded_links" in user_prompt
