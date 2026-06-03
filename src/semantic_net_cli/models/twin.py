"""Pydantic models for semantic twin JSONL network input."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


ALLOWED_TWIN_BASE_TYPES = ("node", "interface", "channel")


class TwinAction(BaseModel):
    """One concrete action record attached to a twin object."""

    model_config = ConfigDict(extra="allow")

    action_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    start_time: str | None = None
    end_time: str | None = None
    status: str | None = None
    reason: str | None = None
    result: str | None = None


class SemanticTwinObject(BaseModel):
    """One JSONL line representing an actual network entity twin."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    relations: dict[str, Any] = Field(default_factory=dict)
    actions: list[TwinAction] = Field(default_factory=list)

    @property
    def base_type(self) -> str:
        return self.type.split(":", 1)[0]

    @property
    def subtype(self) -> str:
        return self.type.split(":", 1)[1]

    @model_validator(mode="after")
    def validate_type(self) -> "SemanticTwinObject":
        parts = self.type.split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("type must use '<base>:<subtype>' format")
        if parts[0] not in ALLOWED_TWIN_BASE_TYPES:
            raise ValueError("type base must be one of node, interface, channel")
        return self


class SemanticTwinGraph(BaseModel):
    """In-memory representation of one semantic twin graph G_k."""

    objects: list[SemanticTwinObject]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "SemanticTwinGraph":
        ids = [item.id for item in self.objects]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate twin object id")
        return self

    @property
    def by_id(self) -> dict[str, SemanticTwinObject]:
        return {item.id: item for item in self.objects}

    def objects_by_base_type(self, base_type: str) -> list[SemanticTwinObject]:
        return [item for item in self.objects if item.base_type == base_type]
