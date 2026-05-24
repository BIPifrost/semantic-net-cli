"""Tests for shared structured-output parsing."""

from __future__ import annotations

from semantic_net_cli.llm.structured_output import parse_agent_output


def test_parse_agent_output_accepts_plain_json_string() -> None:
    output = parse_agent_output(
        "link_quality",
        """
        {
          "agent": "link_quality",
          "status": "degraded",
          "findings": ["Link link-1 is degraded"],
          "evidence": [{"id": "link-1", "reason": "semantic_state=degraded"}],
          "confidence": 0.8
        }
        """,
    )

    assert output.agent == "link_quality"
    assert output.status == "degraded"
    assert output.confidence == 0.8


def test_parse_agent_output_accepts_fenced_json_string() -> None:
    output = parse_agent_output(
        "global_state",
        """```json
        {
          "agent": "global_state",
          "status": "abnormal",
          "findings": ["Network is in an abnormal state"],
          "evidence": [{"id": "link-1", "reason": "multiple abnormal findings"}],
          "confidence": 0.9
        }
        ```""",
    )

    assert output.agent == "global_state"
    assert output.status == "abnormal"
    assert output.findings == ["Network is in an abnormal state"]


def test_parse_agent_output_accepts_dict_with_content_field() -> None:
    output = parse_agent_output(
        "fault_domain",
        {
            "content": """
            {
              "agent": "fault_domain",
              "status": "degraded",
              "findings": ["Primary fault domain is link"],
              "evidence": [{"id": "link-1", "reason": "persistent degradation"}],
              "confidence": 0.75
            }
            """
        },
    )

    assert output.agent == "fault_domain"
    assert output.status == "degraded"
    assert output.evidence[0].id == "link-1"


def test_parse_agent_output_returns_unknown_for_malformed_output() -> None:
    output = parse_agent_output("routing_forwarding", "not-json")

    assert output.agent == "routing_forwarding"
    assert output.status == "unknown"
    assert output.findings == []
    assert output.evidence == []
    assert output.confidence == 0.0
