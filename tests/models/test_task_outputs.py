from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction


def test_back_layer_outputs_match_s_c_u_contracts() -> None:
    state = NetworkState(
        state_id="S_k",
        status="degraded",
        summary="Wireless access segment is degraded.",
        key_fact_ids=["pf-1"],
        confidence=0.82,
    )
    causes = CauseSet(
        cause_set_id="C_k",
        primary_cause="Wireless channel degradation on c_wifi_ap1",
        causes=["interference_increase"],
        evidence_fact_ids=["pf-1"],
        confidence=0.8,
    )
    action = OptimizationAction(
        action_id="U_k",
        recommended_action="Reduce load on c_wifi_ap1 and protect video traffic.",
        target_object_ids=["c_wifi_ap1", "sta1"],
        candidate_actions=["adjust wireless channel", "rate-limit low-priority traffic"],
        reasoning="Cause set points to wireless interference.",
        confidence=0.78,
    )

    assert state.state_id == "S_k"
    assert causes.cause_set_id == "C_k"
    assert action.action_id == "U_k"
