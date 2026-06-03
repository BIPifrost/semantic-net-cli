from pathlib import Path

import pytest

from semantic_net_cli.io.jsonl_loader import load_twin_graph_jsonl


def test_load_twin_graph_jsonl_reads_each_line_as_one_twin_object(tmp_path: Path) -> None:
    path = tmp_path / "network.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}',
                '{"id":"r1_eth0","type":"interface:wired","attributes":{},"relations":{},"actions":[]}',
                '{"id":"c1","type":"channel:wired","attributes":{},"relations":{},"actions":[]}',
            ]
        ),
        encoding="utf-8",
    )

    graph = load_twin_graph_jsonl(path)

    assert len(graph.objects) == 3
    assert graph.by_id["r1"].type == "node:router"


def test_load_twin_graph_jsonl_rejects_old_single_json_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "old.jsonl"
    path.write_text(
        '{"metadata":{"snapshot_id":"old"},"nodes":[],"links":[],"paths":[],"flows":[]}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="JSONL semantic twin"):
        load_twin_graph_jsonl(path)


def test_load_twin_graph_jsonl_reports_line_number_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.jsonl"
    path.write_text(
        '{"id":"r1","type":"node:router","attributes":{},"relations":{},"actions":[]}\nnot-json',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="line 2"):
        load_twin_graph_jsonl(path)
