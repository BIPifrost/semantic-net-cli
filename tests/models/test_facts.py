from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact


def test_intermediate_fact_set_groups_picture_fact_categories() -> None:
    fact = SemanticFact(
        fact_id="pf-1",
        category="performance",
        fact_type="threshold_violation",
        subject_id="c_wifi_ap1",
        summary="WiFi channel loss and retransmission are high.",
        evidence=[{"id": "c_wifi_ap1", "reason": "loss_rate=0.014"}],
        confidence=0.8,
    )

    fact_set = IntermediateFactSet.from_agent_outputs(
        {
            "performance_agent": [fact],
        }
    )

    assert fact_set.fact_set_id == "F_k^mid"
    assert fact_set.performance_facts == [fact]
    assert fact_set.all_facts == [fact]
