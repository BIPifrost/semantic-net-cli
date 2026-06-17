"""Closed-loop control execution and feedback models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


CONTROL_EXECUTION_STATUSES = ("planned", "running", "succeeded", "failed", "skipped", "damped")
PROPAGATION_MODES = ("normal", "damped")
STABILITY_STATES = ("stable", "improving", "damped", "oscillating", "max_iterations")


class MetricObservation(BaseModel):
    """One before/after metric observation produced by control execution feedback."""

    object_id: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    before: Any = None
    after: Any = None
    unit: str | None = None


class MetricUpdate(BaseModel):
    """One metric value update produced by control effect propagation."""

    object_id: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    before: Any = None
    after: Any = None
    reason: str = Field(min_length=1)


class PropagatedControlEffect(BaseModel):
    """Deterministic propagated effect of one executed control action."""

    model_config = ConfigDict(extra="forbid")

    effect_id: str = Field(min_length=1)
    source_execution_id: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    changed_object_ids: list[str] = Field(default_factory=list)
    metric_updates: list[MetricUpdate] = Field(default_factory=list)
    propagation_summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_mode(self) -> "PropagatedControlEffect":
        if self.mode not in PROPAGATION_MODES:
            raise ValueError(f"Unsupported propagation mode: {self.mode}")
        return self


class StabilityAssessment(BaseModel):
    """Closed-loop stability state for one iteration."""

    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(ge=1)
    stability: str = Field(min_length=1)
    terminal_reason: str | None = None
    should_stop: bool = False
    damping_factor: float = Field(ge=0.0, le=1.0)
    oscillation_count: int = Field(ge=0)
    signature: str = Field(min_length=1)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_stability(self) -> "StabilityAssessment":
        if self.stability not in STABILITY_STATES:
            raise ValueError(f"Unsupported stability state: {self.stability}")
        return self


class ControlExecutionRecord(BaseModel):
    """Result of executing, or simulating execution of, one optimization action."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str = Field(min_length=1)
    source_action_id: str = Field(min_length=1)
    executor: str = Field(min_length=1)
    status: str = Field(min_length=1)
    target_object_ids: list[str] = Field(default_factory=list)
    applied_actions: list[str] = Field(default_factory=list)
    feedback_summary: str = Field(min_length=1)
    metric_observations: list[MetricObservation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_status(self) -> "ControlExecutionRecord":
        if self.status not in CONTROL_EXECUTION_STATUSES:
            raise ValueError(f"Unsupported control execution status: {self.status}")
        return self
