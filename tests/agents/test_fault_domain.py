"""Tests for the fault-domain diagnosis agent."""

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


def make_snapshot_for_fault_domain() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-fault-001"},
            "nodes": [
                {
                    "id": "node-a",
                    "type": "host",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.24,
                        "cpu": 0.20,
                        "queue": 0.05,
                    },
                },
                {
                    "id": "node-b",
                    "type": "switch",
                    "role": "aggregation",
                    "semantic_state": "abnormal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.91,
                        "cpu": 0.88,
                        "queue": 0.86,
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
                        "latency": 21.0,
                        "loss": 0.03,
                        "utilization": 0.90,
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


def test_fault_domain_agent_builds_root_cause_context_from_prior_results() -> None:
    from semantic_net_cli.agents.fault_domain import FaultDomainAgent

    snapshot = make_snapshot_for_fault_domain()
    captured_payload: dict = {}

    prior_results = {
        "global_state": AgentOutput.model_validate(
            {
                "agent": "global_state",
                "status": "abnormal",
                "findings": ["The network is abnormal due to aggregation-domain instability"],
                "evidence": [
                    {"id": "node-b", "reason": "aggregation node overloaded"},
                    {"id": "link-ab", "reason": "upstream link degraded"},
                ],
                "confidence": 0.90,
            }
        ),
        "node_bottleneck": AgentOutput.model_validate(
            {
                "agent": "node_bottleneck",
                "status": "abnormal",
                "findings": ["Node node-b is the main bottleneck"],
                "evidence": [{"id": "node-b", "reason": "cpu/utilization/queue are persistently high"}],
                "confidence": 0.91,
            }
        ),
        "link_quality": AgentOutput.model_validate(
            {
                "agent": "link_quality",
                "status": "degraded",
                "findings": ["Link link-ab is degraded"],
                "evidence": [{"id": "link-ab", "reason": "latency, loss, and utilization elevated"}],
                "confidence": 0.82,
            }
        ),
        "flow_impact": AgentOutput.model_validate(
            {
                "agent": "flow_impact",
                "status": "degraded",
                "findings": ["Flow flow-ab is impacted"],
                "evidence": [{"id": "flow-ab", "reason": "depends on node-b and link-ab"}],
                "confidence": 0.85,
            }
        ),
    }

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "fault_domain",
                    "status": "abnormal",
                    "findings": ["The dominant fault domain is aggregation-node overload centered on node-b"],
                    "evidence": [
                        {"id": "node-b", "reason": "repeated abnormal node evidence across prior agents"},
                        {"id": "link-ab", "reason": "secondary degradation likely propagated from node-b"},
                    ],
                    "confidence": 0.89,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = FaultDomainAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, prior_results)

    assert result.agent == "fault_domain"
    assert result.status == "abnormal"
    assert result.evidence[0].id == "node-b"
    user_prompt = captured_payload["user_prompt"]
    assert "dominant_fault_domain" in user_prompt
    assert "node" in user_prompt
    assert "mixed_signal" in user_prompt
    assert "node-b" in user_prompt
    assert "link-ab" in user_prompt
