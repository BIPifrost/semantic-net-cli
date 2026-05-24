"""Shared constants for semantic states, types, roles, and agent status."""

SEMANTIC_STATES = (
    "normal",
    "degraded",
    "congested",
    "abnormal",
)

NODE_TYPES = (
    "host",
    "switch",
    "router",
)

NODE_ROLES = (
    "edge",
    "aggregation",
    "core",
    "exit",
)

LINK_TYPES = (
    "wired",
    "wireless",
    "virtual",
)

AGENT_STATUSES = (
    "normal",
    "degraded",
    "abnormal",
    "unknown",
)
