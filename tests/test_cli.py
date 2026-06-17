"""Tests for the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

from semantic_net_cli.models.control import ControlExecutionRecord
from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph, TwinAction


def write_config(tmp_path: Path) -> Path:
    path = tmp_path / "llm_config.json"
    path.write_text(
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
                "agents": {},
            }
        ),
        encoding="utf-8",
    )
    return path


def make_final_result() -> dict:
    fact = SemanticFact(
        fact_id="performance-1",
        category="performance",
        fact_type="threshold_violation",
        subject_id="c_wifi_ap1",
        summary="Performance is degraded.",
        evidence=[{"id": "c_wifi_ap1", "reason": "loss_rate is elevated"}],
        confidence=0.86,
    )
    return {
        "input_summary": {
            "object_count": 1,
            "node_count": 1,
            "interface_count": 0,
            "channel_count": 0,
        },
        "intermediate_fact_set": IntermediateFactSet.from_agent_outputs({"performance_agent": [fact]}),
        "network_state": NetworkState(
            state_id="S_k",
            status="degraded",
            summary="Network is degraded.",
            key_fact_ids=["performance-1"],
            confidence=0.8,
        ),
        "cause_set": CauseSet(
            cause_set_id="C_k",
            primary_cause="Wireless degradation",
            causes=["interference"],
            evidence_fact_ids=["performance-1"],
            confidence=0.8,
        ),
        "optimization_action": OptimizationAction(
            action_id="U_k",
            recommended_action="Adjust channel.",
            target_object_ids=["c_wifi_ap1"],
            candidate_actions=["adjust channel"],
            reasoning="Interference detected.",
            confidence=0.8,
        ),
        "control_execution": ControlExecutionRecord(
            execution_id="exec-U_k",
            source_action_id="U_k",
            executor="simulated_control_executor",
            status="succeeded",
            target_object_ids=["c_wifi_ap1"],
            applied_actions=["adjust channel"],
            feedback_summary="Simulated execution succeeded.",
            confidence=0.8,
        ),
        "updated_twin_graph": SemanticTwinGraph.model_validate(
            {
                "objects": [
                    {
                        "id": "c_wifi_ap1",
                        "type": "channel:wifi",
                        "attributes": {"status": "degraded"},
                        "relations": {},
                        "actions": [
                            TwinAction(
                                action_id="exec-U_k",
                                action_type="control_execution",
                                status="succeeded",
                                reason="adjust channel",
                                result="Simulated execution succeeded.",
                            ).model_dump()
                        ],
                    }
                ]
            }
        ),
        "next_history_context": {
            "action_count": 1,
            "recent_actions": [{"action_id": "exec-U_k", "object_id": "c_wifi_ap1"}],
        },
    }


def test_cli_accepts_jsonl_semantic_twin_input(monkeypatch, tmp_path, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = tmp_path / "network.jsonl"
    snapshot_path.write_text(
        '{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}',
        encoding="utf-8",
    )
    config_path = write_config(tmp_path)

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            assert state["twin_graph"].objects[0].id == "r1"
            return make_final_result()

    monkeypatch.setattr(cli, "build_workflow", lambda config_path: DummyWorkflow())

    exit_code = cli.main(
        [
            str(snapshot_path),
            "--config",
            str(config_path),
            "--result-dir",
            str(tmp_path / "result"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Closed-Loop Run Summary" in captured.out


def test_cli_rejects_old_json_snapshot(tmp_path, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = tmp_path / "old.json"
    snapshot_path.write_text(
        '{"metadata":{"snapshot_id":"old"},"nodes":[],"links":[],"paths":[],"flows":[]}',
        encoding="utf-8",
    )
    config_path = write_config(tmp_path)

    exit_code = cli.main([str(snapshot_path), "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "JSONL semantic twin" in captured.err


def test_cli_returns_non_zero_for_missing_config(tmp_path, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = tmp_path / "network.jsonl"
    snapshot_path.write_text(
        '{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}',
        encoding="utf-8",
    )

    exit_code = cli.main([str(snapshot_path), "--config", str(tmp_path / "missing.json")])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "LLM config file not found" in captured.err


def test_cli_writes_updated_graph_when_output_path_is_provided(monkeypatch, tmp_path, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = tmp_path / "network.jsonl"
    snapshot_path.write_text(
        '{"id":"c_wifi_ap1","type":"channel:wifi","attributes":{},"relations":{},"actions":[]}',
        encoding="utf-8",
    )
    config_path = write_config(tmp_path)
    output_path = tmp_path / "updated.jsonl"

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            return make_final_result()

    monkeypatch.setattr(cli, "build_workflow", lambda config_path: DummyWorkflow())

    exit_code = cli.main(
        [
            str(snapshot_path),
            "--config",
            str(config_path),
            "--updated-graph-output",
            str(output_path),
            "--result-dir",
            str(tmp_path / "result"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert '"action_id":"exec-U_k"' in output_path.read_text(encoding="utf-8")
    assert "Updated semantic twin graph written" in captured.out


def test_cli_runs_configured_iteration_count_and_writes_result_dir(monkeypatch, tmp_path, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = tmp_path / "network.jsonl"
    snapshot_path.write_text(
        '{"id":"c_wifi_ap1","type":"channel:wifi","attributes":{},"relations":{},"actions":[]}',
        encoding="utf-8",
    )
    config_path = write_config(tmp_path)
    result_dir = tmp_path / "result"

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            return make_final_result()

    monkeypatch.setattr(cli, "build_workflow", lambda config_path: DummyWorkflow())

    exit_code = cli.main(
        [
            str(snapshot_path),
            "--config",
            str(config_path),
            "--max-iterations",
            "2",
            "--result-dir",
            str(result_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Closed-Loop Run Summary" in captured.out
    assert "iteration_count: 2" in captured.out
    assert "stability=" in captured.out
    assert "terminal_reason:" in captured.out
    run_dirs = list(result_dir.iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "iteration_001" / "report.txt").exists()
    assert (run_dirs[0] / "iteration_002" / "topology_changes.json").exists()
    assert (run_dirs[0] / "final_graph.jsonl").exists()
