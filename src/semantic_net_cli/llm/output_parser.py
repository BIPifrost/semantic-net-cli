"""Structured parsing helpers for raw LLM outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AgentOutputParseError(Exception):
    """Raised when one agent returns malformed or incomplete JSON."""

    agent_name: str
    raw_content: str
    parse_error: str

    def __str__(self) -> str:
        return f"agent={self.agent_name}: {self.parse_error}"


def parse_agent_json_output(agent_name: str, raw_response: Any) -> dict[str, Any]:
    """Parse one agent response into a JSON object or raise a rich parse error."""

    content = (
        raw_response["content"]
        if isinstance(raw_response, dict) and "content" in raw_response
        else raw_response
    )
    if not isinstance(content, str):
        raise AgentOutputParseError(
            agent_name=agent_name,
            raw_content=str(content),
            parse_error=f"Expected string content, got {type(content).__name__}",
        )

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AgentOutputParseError(
            agent_name=agent_name,
            raw_content=content,
            parse_error=str(exc),
        ) from exc

    if not isinstance(payload, dict):
        raise AgentOutputParseError(
            agent_name=agent_name,
            raw_content=content,
            parse_error=f"Expected JSON object, got {type(payload).__name__}",
        )

    return payload
