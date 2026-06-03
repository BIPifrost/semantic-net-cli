import json

from semantic_net_cli.agents.understanding_agent import UnderstandingAgent
from semantic_net_cli.llm.client import LLMClient
from semantic_net_cli.llm.config_loader import AgentLLMSettings
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact


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


def test_understanding_agent_outputs_s_k() -> None:
    def transport(payload: dict) -> dict:
        assert payload["agent_name"] == "understanding_agent"
        assert "F_k^mid" in payload["user_prompt"]
        return {
            "content": json.dumps(
                {
                    "state_id": "S_k",
                    "status": "degraded",
                    "summary": "Wireless segment is degraded.",
                    "key_fact_ids": ["performance-1"],
                    "confidence": 0.84,
                }
            )
        }

    result = UnderstandingAgent(LLMClient(transport=transport), settings()).run(make_fact_set(), history_context={})

    assert result.state_id == "S_k"
    assert result.status == "degraded"
