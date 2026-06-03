"""Tests for the two-layer LangGraph workflow assembly."""

from __future__ import annotations

import json
from pathlib import Path

from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.models.twin import SemanticTwinGraph


def write_test_config() -> Path:
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
                    "topology_agent": {},
                    "routing_agent": {},
                    "traffic_agent": {},
                    "performance_agent": {},
                    "node_semantic_agent": {},
                    "understanding_agent": {},
                    "analysis_agent": {},
                    "optimization_agent": {},
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {"id": "ap1", "type": "node:wireless_ap", "attributes": {"status": "active"}, "relations": {"deploys": ["ap1_wlan0"]}, "actions": []},
                {"id": "sta1", "type": "node:wireless_terminal", "attributes": {"status": "active"}, "relations": {"routes_to": [{"dst": "r1", "channels": ["c_wifi_ap1"]}], "transmits_to": [{"dst": "r1", "demand_mbps": 30}]}, "actions": []},
                {"id": "ap1_wlan0", "type": "interface:wireless", "attributes": {"status": "up"}, "relations": {"connected_by": ["c_wifi_ap1"]}, "actions": []},
                {"id": "c_wifi_ap1", "type": "channel:wifi", "attributes": {"status": "degraded"}, "relations": {"connects": ["ap1_wlan0", "sta1_wlan0"]}, "actions": []},
            ]
        }
    )


def test_workflow_runs_picture_architecture_in_order() -> None:
    from semantic_net_cli.workflow.graph import build_workflow

    graph = make_graph()
    call_order = []

    def transport(payload: dict) -> dict:
        name = payload["agent_name"]
        call_order.append(name)
        if name in {
            "topology_agent",
            "routing_agent",
            "traffic_agent",
            "performance_agent",
            "node_semantic_agent",
        }:
            category = name.replace("_agent", "")
            fact_id = "node-semantic-1" if category == "node_semantic" else f"{category}-1"
            return {
                "content": json.dumps(
                    {
                        "facts": [
                            {
                                "fact_id": fact_id,
                                "category": category,
                                "fact_type": "demo",
                                "subject_id": "c_wifi_ap1",
                                "summary": f"{category} fact",
                                "evidence": [{"id": "c_wifi_ap1", "reason": "demo"}],
                                "confidence": 0.8,
                            }
                        ]
                    }
                )
            }
        if name == "understanding_agent":
            return {"content": json.dumps({"state_id": "S_k", "status": "degraded", "summary": "network degraded", "key_fact_ids": ["performance-1"], "confidence": 0.8})}
        if name == "analysis_agent":
            return {"content": json.dumps({"cause_set_id": "C_k", "primary_cause": "wireless channel degraded", "causes": ["interference"], "evidence_fact_ids": ["performance-1"], "confidence": 0.8})}
        if name == "optimization_agent":
            return {"content": json.dumps({"action_id": "U_k", "recommended_action": "adjust channel", "target_object_ids": ["c_wifi_ap1"], "candidate_actions": ["adjust channel"], "reasoning": "interference cause", "confidence": 0.8})}
        raise AssertionError(name)

    workflow = build_workflow(config_path=str(write_test_config()), llm_client=LLMClient(transport=transport))
    result = workflow.invoke({"twin_graph": graph, "history_context": {}})

    assert call_order == [
        "topology_agent",
        "routing_agent",
        "traffic_agent",
        "performance_agent",
        "node_semantic_agent",
        "understanding_agent",
        "analysis_agent",
        "optimization_agent",
    ]
    assert result["intermediate_fact_set"].fact_set_id == "F_k^mid"
    assert result["network_state"].state_id == "S_k"
    assert result["cause_set"].cause_set_id == "C_k"
    assert result["optimization_action"].action_id == "U_k"
