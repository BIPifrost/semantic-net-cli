"""Intermediate semantic facts F_k^mid."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


FACT_CATEGORIES = ("topology", "routing", "traffic", "performance", "node_semantic")


class SemanticFact(BaseModel):
    """One semantic fact extracted by a front-layer perspective agent."""

    fact_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    fact_type: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    evidence: list[dict] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_category(self) -> "SemanticFact":
        if self.category not in FACT_CATEGORIES:
            raise ValueError(f"Unsupported fact category: {self.category}")
        return self


class FactAgentOutput(BaseModel):
    """Strict output shape returned by one front-layer perspective agent."""

    facts: list[SemanticFact] = Field(default_factory=list)


class IntermediateFactSet(BaseModel):
    """Picture-defined intermediate semantic fact set F_k^mid."""

    fact_set_id: str = "F_k^mid"
    topology_facts: list[SemanticFact] = Field(default_factory=list)
    routing_facts: list[SemanticFact] = Field(default_factory=list)
    traffic_facts: list[SemanticFact] = Field(default_factory=list)
    performance_facts: list[SemanticFact] = Field(default_factory=list)
    node_semantic_facts: list[SemanticFact] = Field(default_factory=list)
    all_facts: list[SemanticFact] = Field(default_factory=list)

    @classmethod
    def from_agent_outputs(cls, outputs: dict[str, list[SemanticFact]]) -> "IntermediateFactSet":
        topology_facts = list(outputs.get("topology_agent", []))
        routing_facts = list(outputs.get("routing_agent", []))
        traffic_facts = list(outputs.get("traffic_agent", []))
        performance_facts = list(outputs.get("performance_agent", []))
        node_semantic_facts = list(outputs.get("node_semantic_agent", []))
        all_facts = [
            *topology_facts,
            *routing_facts,
            *traffic_facts,
            *performance_facts,
            *node_semantic_facts,
        ]
        return cls(
            topology_facts=topology_facts,
            routing_facts=routing_facts,
            traffic_facts=traffic_facts,
            performance_facts=performance_facts,
            node_semantic_facts=node_semantic_facts,
            all_facts=all_facts,
        )
