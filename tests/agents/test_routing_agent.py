import json

from semantic_net_cli.agents.routing_agent import RoutingAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.models.twin import SemanticTwinGraph


def settings() -> AgentLLMSettings:
    return AgentLLMSettings(provider="test", model="test", api_key="key", base_url="http://test", temperature=0.2, max_tokens=1000)


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate({"objects": [
        {"id": "ap1", "type": "node:wireless_ap", "attributes": {"role": "access_point", "status": "active", "metrics": {"cpu_usage": 0.41, "queue_length": 22}}, "relations": {"deploys": ["ap1_wlan0"]}, "actions": []},
        {"id": "sta1", "type": "node:wireless_terminal", "attributes": {"role": "mobile_client", "status": "active", "metrics": {}}, "relations": {"deploys": ["sta1_wlan0"], "routes_to": [{"dst": "r1", "next_hop": "ap1", "egress_interface": "sta1_wlan0", "channels": ["c_wifi_ap1"]}], "transmits_to": [{"dst": "r1", "demand_mbps": 30, "service_type": "video"}]}, "actions": []},
        {"id": "ap1_wlan0", "type": "interface:wireless", "attributes": {"media": "wireless", "status": "up", "metrics": {"utilization": 0.68, "rssi_dbm": -42, "snr_db": 31}}, "relations": {"deployed_on": "ap1", "connected_by": ["c_wifi_ap1"]}, "actions": []},
        {"id": "sta1_wlan0", "type": "interface:wireless", "attributes": {"media": "wireless", "status": "degraded", "metrics": {"utilization": 0.72, "rssi_dbm": -71, "snr_db": 15}}, "relations": {"deployed_on": "sta1", "connected_by": ["c_wifi_ap1"]}, "actions": [{"action_id": "a001", "action_type": "disconnection", "reason": "weak_signal"}]},
        {"id": "c_wifi_ap1", "type": "channel:wifi", "attributes": {"status": "degraded", "metrics": {"delay_ms": 14.2, "loss_rate": 0.014, "throughput_mbps": 110, "utilization": 0.76, "retransmission_rate": 0.10, "interference_level": "high"}}, "relations": {"connects": ["ap1_wlan0", "sta1_wlan0"]}, "actions": [{"action_id": "a002", "action_type": "channel_degradation", "status": "running", "reason": "interference_increase"}]},
    ]})


def test_routing_agent_outputs_routing_facts() -> None:
    captured = {}

    def transport(payload: dict) -> dict:
        captured.update(payload)
        return {"content": json.dumps({"facts": [{"fact_id": "routing-1", "category": "routing", "fact_type": "path_anomaly", "subject_id": "sta1", "summary": "Routing fact.", "evidence": [{"id": "sta1", "reason": "routes_to uses degraded channel"}], "confidence": 0.8}]})}

    facts = RoutingAgent(LLMClient(transport=transport), settings()).run(make_graph())

    assert captured["agent_name"] == "routing_agent"
    assert "routes_to" in captured["user_prompt"]
    assert facts[0].category == "routing"
