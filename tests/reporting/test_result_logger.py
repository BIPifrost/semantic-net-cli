import json

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


def make_result() -> dict:
    return {
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
        "updated_twin_graph": make_graph(),
        "next_history_context": {"action_count": 1, "recent_actions": []},
    }


def test_result_logger_writes_iteration_outputs_and_topology_changes(tmp_path) -> None:
    logger = ResultLogger(base_dir=tmp_path, timestamp_provider=lambda: "20260607-120000")
    run_dir = logger.start_run()

    logger.write_iteration(
        run_dir=run_dir,
        iteration_index=1,
        input_graph=make_graph(),
        result=make_result(),
        topology_changes={"changed_object_count": 1, "changes": [{"object_id": "c_wifi_ap1"}]},
        report_text="iteration report",
    )

    iteration_dir = run_dir / "iteration_001"

    assert (iteration_dir / "input_graph.jsonl").exists()
    assert (iteration_dir / "intermediate_fact_set.json").exists()
    assert (iteration_dir / "network_state.json").exists()
    assert (iteration_dir / "cause_set.json").exists()
    assert (iteration_dir / "optimization_action.json").exists()
    assert (iteration_dir / "control_execution.json").exists()
    assert (iteration_dir / "topology_changes.json").exists()
    assert (iteration_dir / "updated_graph.jsonl").exists()
    assert (iteration_dir / "report.txt").read_text(encoding="utf-8") == "iteration report"
    assert json.loads((iteration_dir / "topology_changes.json").read_text(encoding="utf-8"))["changed_object_count"] == 1
