"""Shared agent output models for all semantic-network agents."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from semantic_net_cli.config import AGENT_STATUSES


class EvidenceItem(BaseModel):
    """Evidence object attached to an agent finding."""

    id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class AgentOutput(BaseModel):
    """Shared output shape for all agents."""

    agent: str = Field(min_length=1)
    status: str
    findings: list[str]
    evidence: list[EvidenceItem]
    confidence: float

    @model_validator(mode="after")
    def validate_model(self) -> "AgentOutput":
        if self.status not in AGENT_STATUSES:
            raise ValueError(f"Unsupported agent status: {self.status}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return self

    @classmethod
    def unknown(cls, agent: str) -> "AgentOutput":
        """Create a standard unknown-status output."""

        return cls(
            agent=agent,
            status="unknown",
            findings=[],
            evidence=[],
            confidence=0.0,
        )

    @classmethod
    def empty(cls, agent: str, status: str = "normal") -> "AgentOutput":
        """Create an empty output with an explicit status."""

        return cls(
            agent=agent,
            status=status,
            findings=[],
            evidence=[],
            confidence=1.0 if status == "normal" else 0.5,
        )
