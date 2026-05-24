"""Tests for the shared agent output contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from semantic_net_cli.models.agent_output import AgentOutput


def test_agent_output_accepts_valid_payload() -> None:
    output = AgentOutput.model_validate(
        {
            "agent": "link_quality",
            "status": "degraded",
            "findings": ["Link link-1 is degraded"],
            "evidence": [{"id": "link-1", "reason": "semantic_state=degraded"}],
            "confidence": 0.85,
        }
    )

    assert output.agent == "link_quality"
    assert output.status == "degraded"
    assert output.findings == ["Link link-1 is degraded"]
    assert output.evidence[0].id == "link-1"
    assert output.confidence == 0.85


def test_agent_output_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        AgentOutput.model_validate(
            {
                "agent": "link_quality",
                "status": "warning",
                "findings": [],
                "evidence": [],
                "confidence": 0.5,
            }
        )


def test_agent_output_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError):
        AgentOutput.model_validate(
            {
                "agent": "link_quality",
                "status": "normal",
                "findings": [],
                "evidence": [],
                "confidence": 1.5,
            }
        )


def test_agent_output_unknown_helper_returns_expected_shape() -> None:
    output = AgentOutput.unknown("routing_forwarding")

    assert output.agent == "routing_forwarding"
    assert output.status == "unknown"
    assert output.findings == []
    assert output.evidence == []
    assert output.confidence == 0.0


def test_agent_output_empty_helper_returns_expected_shape() -> None:
    output = AgentOutput.empty("global_state")

    assert output.agent == "global_state"
    assert output.status == "normal"
    assert output.findings == []
    assert output.evidence == []
    assert output.confidence == 1.0
