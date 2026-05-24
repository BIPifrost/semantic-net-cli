"""Tests for the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path


def _write_text(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_cli_prints_report_for_valid_input(monkeypatch, capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = _write_text(
        Path("tests/runtime_cli_snapshot.json"),
        json.dumps(
            {
                "metadata": {"snapshot_id": "cli-001"},
                "nodes": [],
                "links": [],
                "paths": [],
                "flows": [],
            }
        ),
    )
    config_path = _write_text(
        Path("tests/runtime_cli_config.json"),
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
    )

    class DummyWorkflow:
        def invoke(self, state: dict) -> dict:
            assert state["snapshot"].metadata.snapshot_id == "cli-001"
            return {
                "input_summary": {
                    "snapshot_id": "cli-001",
                    "node_count": 0,
                    "link_count": 0,
                    "path_count": 0,
                    "flow_count": 0,
                },
                "global_semantic_state": {
                    "status": "normal",
                    "summary": "The network is normal.",
                    "key_evidence": [],
                },
                "semantic_root_cause": {
                    "primary_cause": "No dominant fault domain detected.",
                    "secondary_causes": [],
                    "reasoning_summary": "No abnormal signals were observed.",
                    "key_evidence": [],
                },
                "closed_loop_control": {
                    "recommended_action": "Keep current policy.",
                    "candidate_actions": ["Keep current policy."],
                    "target_objects": [],
                    "control_reasoning": "No mitigation is required.",
                },
            }

    monkeypatch.setattr(cli, "build_workflow", lambda config_path: DummyWorkflow())

    exit_code = cli.main([str(snapshot_path), "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Input Summary" in captured.out
    assert "Global Semantic State" in captured.out
    assert "Semantic Root-Cause Diagnosis" in captured.out
    assert "Closed-Loop Semantic Control" in captured.out
    assert captured.err == ""


def test_cli_returns_non_zero_for_invalid_schema(capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = _write_text(
        Path("tests/runtime_cli_invalid_snapshot.json"),
        json.dumps(
            {
                "metadata": {"snapshot_id": "cli-invalid-001"},
                "nodes": [],
                "links": [],
                "paths": [],
            }
        ),
    )
    config_path = _write_text(
        Path("tests/runtime_cli_invalid_config.json"),
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
    )

    exit_code = cli.main([str(snapshot_path), "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "Invalid snapshot schema" in captured.err


def test_cli_returns_non_zero_for_missing_config(capsys) -> None:
    from semantic_net_cli import cli

    snapshot_path = _write_text(
        Path("tests/runtime_cli_missing_config_snapshot.json"),
        json.dumps(
            {
                "metadata": {"snapshot_id": "cli-missing-config-001"},
                "nodes": [],
                "links": [],
                "paths": [],
                "flows": [],
            }
        ),
    )

    exit_code = cli.main([str(snapshot_path), "--config", "config/does-not-exist.json"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "LLM config file not found" in captured.err
