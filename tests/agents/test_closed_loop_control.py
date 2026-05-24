"""Tests for the closed-loop semantic control agent."""

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


def make_snapshot_for_control() -> SemanticSnapshot:
    return SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "snapshot-control-001"},
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
                        "cpu": 0.20,
                        "queue": 0.04,
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
                        "utilization": 0.93,
                        "cpu": 0.89,
                        "queue": 0.85,
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
                        "latency": 24.0,
                        "loss": 0.02,
                        "utilization": 0.91,
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


def test_closed_loop_control_agent_builds_action_context_from_diagnosis() -> None:
    from semantic_net_cli.agents.closed_loop_control import ClosedLoopControlAgent

    snapshot = make_snapshot_for_control()
    captured_payload: dict = {}

    prior_results = {
        "global_state": AgentOutput.model_validate(
            {
                "agent": "global_state",
                "status": "abnormal",
                "findings": ["The network is abnormal and service quality is degraded"],
                "evidence": [
                    {"id": "node-b", "reason": "aggregation node overloaded"},
                    {"id": "flow-ab", "reason": "critical flow impacted"},
                ],
                "confidence": 0.88,
            }
        ),
        "fault_domain": AgentOutput.model_validate(
            {
                "agent": "fault_domain",
                "status": "abnormal",
                "findings": ["Primary cause is aggregation-node overload on node-b"],
                "evidence": [
                    {"id": "node-b", "reason": "dominant abnormal object across prior agents"},
                    {"id": "link-ab", "reason": "link degradation is likely downstream effect"},
                ],
                "confidence": 0.90,
            }
        ),
        "flow_impact": AgentOutput.model_validate(
            {
                "agent": "flow_impact",
                "status": "degraded",
                "findings": ["Flow flow-ab is impacted"],
                "evidence": [{"id": "flow-ab", "reason": "depends on node-b and link-ab"}],
                "confidence": 0.84,
            }
        ),
    }

    def transport(payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "content": json.dumps(
                {
                    "agent": "closed_loop_control",
                    "status": "abnormal",
                    "findings": [
                        "Recommend load-shedding or path adjustment around node-b before service degradation spreads"
                    ],
                    "evidence": [
                        {"id": "node-b", "reason": "target object for relief action"},
                        {"id": "flow-ab", "reason": "critical flow should be protected first"},
                    ],
                    "confidence": 0.87,
                }
            )
        }

    class DummyClient:
        def __init__(self) -> None:
            self._transport = transport

        def invoke(self, **kwargs):
            return self._transport(kwargs)

    agent = ClosedLoopControlAgent(
        llm_client=DummyClient(),
        structured_output=parse_agent_output,
        settings=make_settings(),
    )

    result = agent.run(snapshot, prior_results)

    assert result.agent == "closed_loop_control"
    assert result.status == "abnormal"
    assert result.evidence[0].id == "node-b"
    user_prompt = captured_payload["user_prompt"]
    assert "recommended_action_hint" in user_prompt
    assert "target_object_ids" in user_prompt
    assert "node-b" in user_prompt
    assert "flow-ab" in user_prompt
    assert "do_not_execute" in user_prompt
