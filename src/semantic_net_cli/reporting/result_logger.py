"""Write closed-loop run artifacts under result/<run-timestamp>/."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from semantic_net_cli.io.jsonl_writer import write_twin_graph_jsonl
from semantic_net_cli.models.twin import SemanticTwinGraph


class ResultLogger:
    """Persist one run and its per-iteration artifacts."""

    def __init__(
        self,
        base_dir: str | Path = "result",
        timestamp_provider: Callable[[], str] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.timestamp_provider = timestamp_provider or _default_timestamp

    def start_run(self) -> Path:
        run_dir = self.base_dir / self.timestamp_provider()
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir

    def write_iteration(
        self,
        *,
        run_dir: Path,
        iteration_index: int,
        input_graph: SemanticTwinGraph,
        result: dict,
        topology_changes: dict,
        report_text: str,
    ) -> Path:
        iteration_dir = run_dir / f"iteration_{iteration_index:03d}"
        iteration_dir.mkdir(parents=True, exist_ok=False)
        write_twin_graph_jsonl(input_graph, iteration_dir / "input_graph.jsonl")
        _write_json(
            iteration_dir / "intermediate_fact_set.json",
            result["intermediate_fact_set"].model_dump(),
        )
        _write_json(iteration_dir / "network_state.json", result["network_state"].model_dump())
        _write_json(iteration_dir / "cause_set.json", result["cause_set"].model_dump())
        _write_json(
            iteration_dir / "optimization_action.json",
            result["optimization_action"].model_dump(),
        )
        _write_json(
            iteration_dir / "control_execution.json",
            result["control_execution"].model_dump(),
        )
        _write_json(iteration_dir / "topology_changes.json", topology_changes)
        write_twin_graph_jsonl(result["updated_twin_graph"], iteration_dir / "updated_graph.jsonl")
        (iteration_dir / "report.txt").write_text(report_text, encoding="utf-8")
        return iteration_dir

    def write_run_summary(
        self,
        *,
        run_dir: Path,
        summary: dict,
        final_graph: SemanticTwinGraph,
    ) -> None:
        _write_json(run_dir / "run_summary.json", summary)
        write_twin_graph_jsonl(final_graph, run_dir / "final_graph.jsonl")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _default_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")
