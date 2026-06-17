"""CLI entrypoint for the semantic network analysis prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from semantic_net_cli.control.loop import run_control_loop
from semantic_net_cli.io.jsonl_loader import load_twin_graph_jsonl
from semantic_net_cli.io.jsonl_writer import write_twin_graph_jsonl
from semantic_net_cli.reporting.result_logger import ResultLogger
from semantic_net_cli.workflow.graph import build_workflow


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"LLM config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        twin_graph = _load_twin_graph(Path(args.snapshot))
    except FileNotFoundError:
        print(f"JSONL semantic twin file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Invalid JSONL semantic twin input: {exc}", file=sys.stderr)
        return 2

    try:
        workflow = build_workflow(str(config_path))
        loop_result = run_control_loop(
            workflow=workflow,
            initial_graph=twin_graph,
            max_iterations=args.max_iterations,
            logger=ResultLogger(base_dir=args.result_dir),
        )
        _print_loop_summary(loop_result)
        if args.updated_graph_output:
            write_twin_graph_jsonl(loop_result["final_graph"], Path(args.updated_graph_output))
            print(f"Updated semantic twin graph written: {args.updated_graph_output}")
        return 0
    except Exception as exc:
        print(f"Workflow execution failed: {exc}", file=sys.stderr)
        return 3


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="semantic-net-cli",
        description="Run the semantic network multi-agent analysis workflow on one JSONL semantic twin graph.",
    )
    parser.add_argument("snapshot", help="Path to the semantic twin JSONL file.")
    parser.add_argument(
        "--config",
        default="config/llm_config.example.json",
        help="Path to the shared LLM configuration JSON file.",
    )
    parser.add_argument(
        "--updated-graph-output",
        help="Optional path to write the feedback-updated semantic twin JSONL graph G_k+1.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=1,
        help="Number of closed-loop iterations to run. Must be >= 1.",
    )
    parser.add_argument(
        "--result-dir",
        default="result",
        help="Directory where timestamped closed-loop run artifacts are written.",
    )
    return parser


def _load_twin_graph(path: Path):
    """Load and validate one semantic twin graph from disk."""

    return load_twin_graph_jsonl(path)


def _print_loop_summary(loop_result: dict) -> None:
    """Print the compact terminal summary for a closed-loop run."""

    print("Closed-Loop Run Summary")
    print(f"run_dir: {loop_result['run_dir']}")
    print(f"iteration_count: {loop_result['iteration_count']}")
    print()
    for item in loop_result["iteration_summaries"]:
        print(
            f"[{item['iteration']}/{loop_result['iteration_count']}] "
            f"S_k={item['network_status']} | "
            f"C_k={item['primary_cause']} | "
            f"U_k={item['recommended_action']} | "
            f"execution={item['execution_status']} | "
            f"stability={item.get('stability', 'unknown')} | "
            f"changed_objects={item['changed_object_count']}"
        )
    print()
    print(f"final_graph: {loop_result['run_dir'] / 'final_graph.jsonl'}")
    print(f"terminal_reason: {loop_result.get('terminal_reason', 'unknown')}")


if __name__ == "__main__":
    raise SystemExit(main())
