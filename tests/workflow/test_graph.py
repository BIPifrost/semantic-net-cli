"""Tests for the LangGraph workflow assembly."""

from __future__ import annotations

import json
from pathlib import Path
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.models.schema import SemanticSnapshot


def _write_test_config() -> Path:
    config_path = Path("tests/workflow/runtime_llm_config.json")
    config_path.write_text(
        json.dumps(
            {
                "global": {
                    "provider": "openai",
                    "model": "gpt-4.1-mini",
                    "api_key": "placeholder-key",
                    "base_url": "https://api.openai.com/v1",
                    "temperature": 0.2,
                    "max_tokens": 1200,
                },
                "agents": {
                    "topology_dependency": {},
                    "link_quality": {},
                    "routing_forwarding": {},
                    "node_bottleneck": {},
                    "flow_impact": {},
                    "global_state": {},
                    "fault_domain": {},
                    "closed_loop_control": {},
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_workflow_runs_agents_in_fixed_order_and_builds_final_result() -> None:
    from semantic_net_cli.workflow.graph import build_workflow

    config_path = _write_test_config()

    snapshot = SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "workflow-001"},
            "nodes": [
                {
                    "id": "node-a",
                    "type": "host",
                    "role": "edge",
                    "semantic_state": "normal",
                    "metrics": {
                        "latency": None,
                        "loss": None,
                        "utilization": 0.25,
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
                        "utilization": 0.92,
                        "cpu": 0.90,
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
                        "latency": 22.0,
                        "loss": 0.02,
                        "utilization": 0.89,
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

    call_order: list[str] = []

    def transport(payload: dict) -> dict:
        agent_name = payload["agent_name"]
        call_order.append(agent_name)

        responses = {
            "topology_dependency": {
                "agent": "topology_dependency",
                "status": "normal",
                "findings": ["Topology dependencies are consistent"],
                "evidence": [{"id": "path-ab", "reason": "flow-ab maps to an existing path"}],
                "confidence": 0.90,
            },
            "link_quality": {
                "agent": "link_quality",
                "status": "degraded",
                "findings": ["Link link-ab is degraded"],
                "evidence": [{"id": "link-ab", "reason": "latency, loss, and utilization elevated"}],
                "confidence": 0.86,
            },
            "routing_forwarding": {
                "agent": "routing_forwarding",
                "status": "degraded",
                "findings": ["Path path-ab is degraded"],
                "evidence": [{"id": "path-ab", "reason": "path semantic_state is degraded"}],
                "confidence": 0.84,
            },
            "node_bottleneck": {
                "agent": "node_bottleneck",
                "status": "abnormal",
                "findings": ["Node node-b is a bottleneck"],
                "evidence": [{"id": "node-b", "reason": "cpu/utilization/queue are high"}],
                "confidence": 0.91,
            },
            "flow_impact": {
                "agent": "flow_impact",
                "status": "degraded",
                "findings": ["Flow flow-ab is impacted"],
                "evidence": [{"id": "flow-ab", "reason": "depends on degraded path-ab"}],
                "confidence": 0.85,
            },
            "global_state": {
                "agent": "global_state",
                "status": "abnormal",
                "findings": ["The whole network is abnormal"],
                "evidence": [{"id": "node-b", "reason": "aggregation bottleneck dominates global state"}],
                "confidence": 0.89,
            },
            "fault_domain": {
                "agent": "fault_domain",
                "status": "abnormal",
                "findings": ["Primary fault domain is aggregation-node overload at node-b"],
                "evidence": [{"id": "node-b", "reason": "dominant abnormal object across prior agents"}],
                "confidence": 0.88,
            },
            "closed_loop_control": {
                "agent": "closed_loop_control",
                "status": "abnormal",
                "findings": ["Recommend relieving load on node-b and protecting flow-ab"],
                "evidence": [{"id": "node-b", "reason": "best control target for immediate mitigation"}],
                "confidence": 0.87,
            },
        }
        return {"content": json.dumps(responses[agent_name])}

    try:
        workflow = build_workflow(
            config_path=str(config_path),
            llm_client=LLMClient(transport=transport),
        )

        result = workflow.invoke({"snapshot": snapshot})
    finally:
        pass

    assert call_order == [
        "topology_dependency",
        "link_quality",
        "routing_forwarding",
        "node_bottleneck",
        "flow_impact",
        "global_state",
        "fault_domain",
        "closed_loop_control",
    ]
    assert result["input_summary"]["snapshot_id"] == "workflow-001"
    assert result["global_semantic_state"]["status"] == "abnormal"
    assert "whole network is abnormal" in result["global_semantic_state"]["summary"]
    assert result["semantic_root_cause"]["primary_cause"].startswith("Primary fault domain")
    assert result["closed_loop_control"]["recommended_action"].startswith("Recommend relieving load")
    assert result["agent_results"]["node_bottleneck"].status == "abnormal"


def test_workflow_keeps_running_when_one_agent_returns_unknown() -> None:
    from semantic_net_cli.workflow.graph import build_workflow

    config_path = _write_test_config()

    snapshot = SemanticSnapshot.model_validate(
        {
            "metadata": {"snapshot_id": "workflow-unknown-001"},
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
                        "queue": 0.03,
                    },
                }
            ],
            "links": [],
            "paths": [],
            "flows": [],
        }
    )

    def transport(payload: dict) -> dict:
        if payload["agent_name"] == "routing_forwarding":
            return {"content": "not-json"}
        return {
            "content": json.dumps(
                {
                    "agent": payload["agent_name"],
                    "status": "normal",
                    "findings": [f"{payload['agent_name']} ok"],
                    "evidence": [],
                    "confidence": 0.80,
                }
            )
        }

    try:
        workflow = build_workflow(
            config_path=str(config_path),
            llm_client=LLMClient(transport=transport),
        )

        result = workflow.invoke({"snapshot": snapshot})
    finally:
        pass

    assert result["agent_results"]["routing_forwarding"].status == "unknown"
    assert result["global_semantic_state"]["status"] in {"normal", "unknown"}
    assert "closed_loop_control" in result["agent_results"]
