import json

from semantic_net_cli.agents.optimization_agent import OptimizationAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import CauseSet


def settings() -> AgentLLMSettings:
    return AgentLLMSettings(provider="test", model="test", api_key="key", base_url="http://test", temperature=0.2, max_tokens=1000)


def make_fact_set() -> IntermediateFactSet:
    fact = SemanticFact(
        fact_id="performance-1",
        category="performance",
        fact_type="threshold_violation",
        subject_id="c_wifi_ap1",
        summary="c_wifi_ap1 is degraded.",
        evidence=[{"id": "c_wifi_ap1", "reason": "loss_rate is elevated"}],
        confidence=0.86,
    )
    return IntermediateFactSet.from_agent_outputs({"performance_agent": [fact]})


def test_optimization_agent_outputs_u_k() -> None:
    cause_set = CauseSet(
        cause_set_id="C_k",
        primary_cause="Wireless channel degradation on c_wifi_ap1",
        causes=["interference_increase"],
        evidence_fact_ids=["performance-1"],
        confidence=0.82,
    )

    def transport(payload: dict) -> dict:
        assert payload["agent_name"] == "optimization_agent"
        assert "do_not_execute" in payload["user_prompt"]
        return {
            "content": json.dumps(
                {
                    "action_id": "U_k",
                    "recommended_action": "Adjust wireless channel and protect video traffic.",
                    "target_object_ids": ["c_wifi_ap1", "sta1"],
                    "candidate_actions": ["adjust wireless channel"],
                    "reasoning": "Cause set points to wireless interference.",
                    "confidence": 0.78,
                }
            )
        }

    result = OptimizationAgent(LLMClient(transport=transport), settings()).run(cause_set, make_fact_set())

    assert result.action_id == "U_k"
    assert result.target_object_ids == ["c_wifi_ap1", "sta1"]
