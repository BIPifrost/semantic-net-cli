"""Pydantic models for the fixed semantic-network snapshot schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from semantic_net_cli.config import LINK_TYPES, NODE_ROLES, NODE_TYPES, SEMANTIC_STATES


class Metadata(BaseModel):
    """Metadata for a single semantic-network snapshot."""

    model_config = ConfigDict(extra="allow")

    snapshot_id: str = Field(min_length=1)


class Metrics(BaseModel):
    """Shared metrics object used across nodes and links."""

    latency: float | None
    loss: float | None
    utilization: float | None
    cpu: float | None
    queue: float | None


class Node(BaseModel):
    """Semantic node object."""

    id: str = Field(min_length=1)
    type: str
    role: str
    semantic_state: str
    metrics: Metrics

    def model_post_init(self, __context: Any) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(f"Unsupported node type: {self.type}")
        if self.role not in NODE_ROLES:
            raise ValueError(f"Unsupported node role: {self.role}")
        if self.semantic_state not in SEMANTIC_STATES:
            raise ValueError(f"Unsupported semantic state: {self.semantic_state}")


class Link(BaseModel):
    """Semantic link object."""

    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: str
    semantic_state: str
    metrics: Metrics

    def model_post_init(self, __context: Any) -> None:
        if self.type not in LINK_TYPES:
            raise ValueError(f"Unsupported link type: {self.type}")
        if self.semantic_state not in SEMANTIC_STATES:
            raise ValueError(f"Unsupported semantic state: {self.semantic_state}")


class Path(BaseModel):
    """Semantic path object."""

    id: str = Field(min_length=1)
    node_ids: list[str]
    link_ids: list[str]
    semantic_state: str

    def model_post_init(self, __context: Any) -> None:
        if self.semantic_state not in SEMANTIC_STATES:
            raise ValueError(f"Unsupported semantic state: {self.semantic_state}")


class Flow(BaseModel):
    """Semantic business-flow object."""

    id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    path_id: str = Field(min_length=1)
    semantic_state: str
    importance: str = Field(min_length=1)

    def model_post_init(self, __context: Any) -> None:
        if self.semantic_state not in SEMANTIC_STATES:
            raise ValueError(f"Unsupported semantic state: {self.semantic_state}")


class SemanticSnapshot(BaseModel):
    """Top-level fixed semantic-network snapshot."""

    metadata: Metadata
    nodes: list[Node]
    links: list[Link]
    paths: list[Path]
    flows: list[Flow]
