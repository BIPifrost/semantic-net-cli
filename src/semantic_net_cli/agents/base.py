"""Shared agent interface for the semantic network analysis pipeline."""

from __future__ import annotations

import json
from typing import Any

from semantic_net_cli.models.facts import SemanticFact


def parse_fact_response(raw_response: Any) -> list[SemanticFact]:
    """Parse a front-layer LLM response into semantic facts."""

    content = (
        raw_response["content"]
        if isinstance(raw_response, dict) and "content" in raw_response
        else raw_response
    )
    payload = json.loads(content) if isinstance(content, str) else content
    return [SemanticFact.model_validate(item) for item in payload.get("facts", [])]
