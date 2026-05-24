"""Shared structured-output parsing for LLM-backed agents."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from semantic_net_cli.models.agent_output import AgentOutput


def parse_agent_output(agent_name: str, raw_response: Any) -> AgentOutput:
    """Parse raw LLM output into the shared agent-output contract."""

    try:
        payload = _normalize_payload(raw_response)
        return AgentOutput.model_validate(payload)
    except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
        return AgentOutput.unknown(agent_name)


def _normalize_payload(raw_response: Any) -> dict[str, Any]:
    """Normalize raw provider output into a plain dictionary."""

    if isinstance(raw_response, dict):
        if "content" in raw_response and isinstance(raw_response["content"], str):
            return _normalize_payload(raw_response["content"])
        return _coerce_minimal_fields(raw_response)

    if isinstance(raw_response, str):
        normalized = raw_response.strip()
        if normalized.startswith("```"):
            normalized = _strip_fenced_block(normalized)
        return _coerce_minimal_fields(json.loads(normalized))

    raise TypeError(f"Unsupported response type: {type(raw_response)!r}")


def _strip_fenced_block(text: str) -> str:
    """Strip a fenced code block wrapper if present."""

    lines = [line.strip() for line in text.splitlines()]
    if not lines:
        raise ValueError("Empty fenced block")
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _coerce_minimal_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply narrow compatibility fixes without becoming a general repair layer."""

    normalized = dict(payload)
    if isinstance(normalized.get("findings"), str):
        normalized["findings"] = [normalized["findings"]]
    return normalized
