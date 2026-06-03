"""Tests for the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

from semantic_net_cli.models.facts import IntermediateFactSet, SemanticFact
from semantic_net_cli.models.task_outputs import CauseSet, NetworkState, OptimizationAction


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

    exit_code = cli.main([str(snapshot_path), "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Intermediate Semantic Fact Set" in captured.out


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
