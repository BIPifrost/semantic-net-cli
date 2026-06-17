"""Shared agent interface for the semantic network analysis pipeline."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.llm.output_parser import parse_agent_json_output
from semantic_net_cli.models.facts import SemanticFact


def parse_fact_response(raw_response: Any) -> list[SemanticFact]:
    """Parse a front-layer LLM response into semantic facts."""

    payload = parse_agent_json_output("front_layer_agent", raw_response)
    return [SemanticFact.model_validate(item) for item in payload.get("facts", [])]
