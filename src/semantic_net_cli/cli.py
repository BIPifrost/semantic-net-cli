"""CLI entrypoint for the semantic network analysis prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from semantic_net_cli.io.jsonl_loader import load_twin_graph_jsonl
from semantic_net_cli.reporting.formatter import format_report
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
        final_result = workflow.invoke({"twin_graph": twin_graph, "history_context": {}})
        print(format_report(final_result))
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
    return parser


def _load_twin_graph(path: Path):
    """Load and validate one semantic twin graph from disk."""

    return load_twin_graph_jsonl(path)


if __name__ == "__main__":
    raise SystemExit(main())
