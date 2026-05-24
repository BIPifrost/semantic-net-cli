"""CLI entrypoint for the semantic network analysis prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from semantic_net_cli.models.schema import SemanticSnapshot
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
        snapshot = _load_snapshot(Path(args.snapshot))
    except FileNotFoundError:
        print(f"Snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print(f"Invalid snapshot schema: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid snapshot JSON: {exc}", file=sys.stderr)
        return 2

    try:
        workflow = build_workflow(str(config_path))
        final_result = workflow.invoke({"snapshot": snapshot})
        print(format_report(final_result))
        return 0
    except Exception as exc:
        print(f"Workflow execution failed: {exc}", file=sys.stderr)
        return 3


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="semantic-net-cli",
        description="Run the semantic network multi-agent analysis workflow on one JSON snapshot.",
    )
    parser.add_argument("snapshot", help="Path to the semantic snapshot JSON file.")
    parser.add_argument(
        "--config",
        default="config/llm_config.example.json",
        help="Path to the shared LLM configuration JSON file.",
    )
    return parser


def _load_snapshot(path: Path) -> SemanticSnapshot:
    """Load and validate one semantic snapshot from disk."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return SemanticSnapshot.model_validate(data)


if __name__ == "__main__":
    raise SystemExit(main())
