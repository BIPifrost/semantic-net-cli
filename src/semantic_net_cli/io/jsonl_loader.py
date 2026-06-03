"""UTF-8 JSONL loader for semantic twin network graphs."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from semantic_net_cli.models.twin import SemanticTwinGraph, SemanticTwinObject


OLD_SNAPSHOT_KEYS = {"metadata", "nodes", "links", "paths", "flows"}


def load_twin_graph_jsonl(path: str | Path) -> SemanticTwinGraph:
    """Load one semantic twin graph from a UTF-8 JSONL file."""

    source = Path(path)
    objects: list[SemanticTwinObject] = []

    for line_number, raw_line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL semantic twin input at line {line_number}: {exc}") from exc

        if isinstance(payload, dict) and OLD_SNAPSHOT_KEYS.issubset(payload.keys()):
            raise ValueError("Input must be JSONL semantic twin objects, not old snapshot JSON")

        try:
            objects.append(SemanticTwinObject.model_validate(payload))
        except ValidationError as exc:
            raise ValueError(f"Invalid JSONL semantic twin object at line {line_number}: {exc}") from exc

    if not objects:
        raise ValueError("JSONL semantic twin input must contain at least one object")

    try:
        return SemanticTwinGraph.model_validate({"objects": objects})
    except ValidationError as exc:
        raise ValueError(f"Invalid JSONL semantic twin graph: {exc}") from exc
