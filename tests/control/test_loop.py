from semantic_net_cli.control.loop import run_control_loop
from semantic_net_cli.control.stability import StabilityMonitor
from semantic_net_cli.llm.output_parser import AgentOutputParseError
from semantic_net_cli.models.control import ControlExecutionRecord
from semantic_net_cli.models.facts import IntermediateFactSet
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph
from semantic_net_cli.reporting.result_logger import ResultLogger


def make_graph() -> SemanticTwinGraph:
    return SemanticTwinGraph.model_validate(
        {
            "objects": [
                {
                    "id": "c_wifi_ap1",
                    "type": "channel:wifi",
                    "attributes": {
                        "metrics": {
                            "loss_rate": 0.014,
                            "retransmission_rate": 0.10,
                            "throughput_mbps": 110,
                        }
                    },
                    "relations": {},
                    "actions": [],
                }
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


def test_control_loop_writes_stability_and_stops_on_stable_state(tmp_path) -> None:
    calls = []

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            calls.append(state["twin_graph"])
            result = make_result(state["twin_graph"])
            result["network_state"] = NetworkState(status="normal", summary="normal", confidence=0.9)
            result["cause_set"] = CauseSet(primary_cause="none", confidence=0.9)
            result["optimization_action"] = OptimizationAction(
                recommended_action="no further action",
                target_object_ids=[],
                reasoning="normal",
                confidence=0.9,
            )
            result["control_execution"] = ControlExecutionRecord(
                execution_id="exec-U_k",
                source_action_id="U_k",
                executor="simulated_control_executor",
                status="skipped",
                target_object_ids=[],
                applied_actions=["no further action"],
                feedback_summary="skipped",
                confidence=0.9,
            )
            return result

    result = run_control_loop(
        workflow=DummyWorkflow(),
        initial_graph=make_graph(),
        max_iterations=5,
        logger=ResultLogger(base_dir=tmp_path, timestamp_provider=lambda: "20260617-120000"),
        stability_monitor=StabilityMonitor(stable_window=2),
    )

    assert len(calls) == 2
    assert result["terminal_reason"] == "stable_state_reached"
    assert (result["run_dir"] / "iteration_001" / "stability_assessment.json").exists()
    assert (result["run_dir"] / "iteration_001" / "effect_propagation.json").exists()


def test_control_loop_enters_damped_mode_for_oscillation(tmp_path) -> None:
    signatures = [
        ("degraded", "wireless_A", "shift_to_B", ["c_wifi_ap1"]),
        ("degraded", "wireless_B", "shift_to_A", ["c_wifi_ap1"]),
        ("degraded", "wireless_A", "shift_to_B", ["c_wifi_ap1"]),
        ("degraded", "wireless_B", "shift_to_A", ["c_wifi_ap1"]),
    ]

    class DummyWorkflow:
        def __init__(self) -> None:
            self.index = 0

        def invoke(self, state: dict) -> dict:
            status, cause, action, targets = signatures[self.index]
            self.index += 1
            result = make_result(state["twin_graph"])
            result["network_state"] = NetworkState(status=status, summary=status, confidence=0.8)
            result["cause_set"] = CauseSet(primary_cause=cause, confidence=0.8)
            result["optimization_action"] = OptimizationAction(
                recommended_action=action,
                target_object_ids=targets,
                reasoning="oscillation test",
                confidence=0.8,
            )
            result["control_execution"] = ControlExecutionRecord(
                execution_id="exec-U_k",
                source_action_id="U_k",
                executor="simulated_control_executor",
                status="succeeded",
                target_object_ids=targets,
                applied_actions=[action],
                feedback_summary="accepted",
                confidence=0.8,
            )
            return result

    result = run_control_loop(
        workflow=DummyWorkflow(),
        initial_graph=make_graph(),
        max_iterations=4,
        logger=ResultLogger(base_dir=tmp_path, timestamp_provider=lambda: "20260617-120000"),
        stability_monitor=StabilityMonitor(stable_window=2),
    )

    assert result["iteration_summaries"][-1]["stability"] == "damped"
    assert result["iteration_summaries"][-1]["damping_factor"] == 0.5


def test_control_loop_saves_raw_llm_output_when_agent_json_parse_fails(tmp_path) -> None:
    raw_content = '{"summary": "unterminated'

    class FailingWorkflow:
        def invoke(self, state: dict) -> dict:
            raise AgentOutputParseError(
                agent_name="analysis_agent",
                raw_content=raw_content,
                parse_error="Unterminated string starting at: line 1 column 13",
            )

    logger = ResultLogger(base_dir=tmp_path, timestamp_provider=lambda: "20260617-120000")

    try:
        run_control_loop(
            workflow=FailingWorkflow(),
            initial_graph=make_graph(),
            max_iterations=3,
            logger=logger,
        )
    except AgentOutputParseError:
        pass

    debug_dir = tmp_path / "20260617-120000" / "debug" / "raw_llm_outputs" / "iteration_001"
    assert (debug_dir / "analysis_agent.txt").read_text(encoding="utf-8") == raw_content
    assert "Unterminated string" in (debug_dir / "parse_error.json").read_text(encoding="utf-8")
