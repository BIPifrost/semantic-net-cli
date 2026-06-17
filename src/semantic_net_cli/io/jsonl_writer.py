"""UTF-8 JSONL writer for semantic twin network graphs."""

from __future__ import annotations

import json
from pathlib import Path

from semantic_net_cli.models.twin import SemanticTwinGraph


def write_twin_graph_jsonl(graph: SemanticTwinGraph, path: str | Path) -> None:
    """Write one semantic twin object per line using UTF-8 JSONL."""

    target = Path(path)
    lines = [
        json.dumps(item.model_dump(), ensure_ascii=False, separators=(",", ":"))
        for item in graph.objects
    ]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
