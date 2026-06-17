"""Closed-loop control execution and feedback models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


CONTROL_EXECUTION_STATUSES = ("planned", "running", "succeeded", "failed", "skipped")


class MetricObservation(BaseModel):
    """One before/after metric observation produced by control execution feedback."""

    object_id: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    before: Any = None
    after: Any = None
    unit: str | None = None


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
