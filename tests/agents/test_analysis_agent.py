import json

from semantic_net_cli.agents.analysis_agent import AnalysisAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import NetworkState


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


def test_analysis_agent_outputs_c_k() -> None:
    state = NetworkState(
        state_id="S_k",
        status="degraded",
        summary="Wireless segment is degraded.",
        key_fact_ids=["performance-1"],
        confidence=0.84,
    )

    def transport(payload: dict) -> dict:
        assert payload["agent_name"] == "analysis_agent"
        assert "S_k" in payload["user_prompt"]
        return {
            "content": json.dumps(
                {
                    "cause_set_id": "C_k",
                    "primary_cause": "Wireless channel degradation on c_wifi_ap1",
                    "causes": ["interference_increase"],
                    "evidence_fact_ids": ["performance-1"],
                    "confidence": 0.82,
                }
            )
        }

    result = AnalysisAgent(LLMClient(transport=transport), settings()).run(state, make_fact_set())

    assert result.cause_set_id == "C_k"
    assert result.primary_cause.startswith("Wireless channel")
