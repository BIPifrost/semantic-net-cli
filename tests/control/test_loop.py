from semantic_net_cli.control.loop import run_control_loop
from semantic_net_cli.models.control import ControlExecutionRecord
from semantic_net_cli.models.facts import IntermediateFactSet
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph
from semantic_net_cli.reporting.result_logger import ResultLogger


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {"id": "c_wifi_ap1", "type": "channel:wifi", "attributes": {}, "relations": {}, "actions": []}
            ]
        }
    )


def make_result(graph: SemanticTwinGraph) -> dict:
    updated = graph.model_copy(deep=True)
    return {
        "input_summary": {
            "object_count": len(graph.objects),
            "node_count": len(graph.objects_by_base_type("node")),
            "interface_count": len(graph.objects_by_base_type("interface")),
            "channel_count": len(graph.objects_by_base_type("channel")),
        },
        "intermediate_fact_set": IntermediateFactSet(),
        "network_state": NetworkState(status="degraded", summary="network degraded", confidence=0.8),
        "cause_set": CauseSet(primary_cause="wireless degradation", confidence=0.8),
        "optimization_action": OptimizationAction(
            recommended_action="adjust channel",
            target_object_ids=["c_wifi_ap1"],
            reasoning="interference",
            confidence=0.8,
        ),
        "control_execution": ControlExecutionRecord(
            execution_id="exec-U_k",
            source_action_id="U_k",
            executor="simulated_control_executor",
            status="succeeded",
            target_object_ids=["c_wifi_ap1"],
            applied_actions=["adjust channel"],
            feedback_summary="accepted",
            confidence=0.8,
        ),
        "updated_twin_graph": updated,
        "next_history_context": {"action_count": 1, "recent_actions": []},
    }


def test_run_control_loop_executes_exact_max_iterations(tmp_path) -> None:
    calls = []

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            calls.append(state["twin_graph"])
            return make_result(state["twin_graph"])

    result = run_control_loop(
        workflow=DummyWorkflow(),
        initial_graph=make_graph(),
        max_iterations=3,
        logger=ResultLogger(base_dir=tmp_path, timestamp_provider=lambda: "20260607-120000"),
    )

    assert len(calls) == 3
    assert result["iteration_count"] == 3
    assert (result["run_dir"] / "iteration_001" / "report.txt").exists()
    assert (result["run_dir"] / "iteration_003" / "updated_graph.jsonl").exists()
    assert (result["run_dir"] / "final_graph.jsonl").exists()
