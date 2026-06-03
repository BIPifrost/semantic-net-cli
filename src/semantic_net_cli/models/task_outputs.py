"""Back-layer task output models S_k, C_k, and U_k."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NetworkState(BaseModel):
    """Understanding Agent output: current network state S_k."""

    state_id: str = "S_k"
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    key_fact_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class CauseSet(BaseModel):
    """Analysis Agent output: cause set C_k."""

    cause_set_id: str = "C_k"
    primary_cause: str = Field(min_length=1)
    causes: list[str] = Field(default_factory=list)
    evidence_fact_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class OptimizationAction(BaseModel):
    """Optimization Agent output: optimization action U_k."""

    action_id: str = "U_k"
    recommended_action: str = Field(min_length=1)
    target_object_ids: list[str] = Field(default_factory=list)
    candidate_actions: list[str] = Field(default_factory=list)
    reasoning: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
