"""Build structured topology change summaries between semantic twin graphs."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.models.twin import SemanticTwinGraph


def build_topology_change_set(before: SemanticTwinGraph, after: SemanticTwinGraph) -> dict[str, Any]:
    """Return object-level changes introduced by feedback application."""

    before_by_id = before.by_id
    changes: list[dict[str, Any]] = []

    for after_obj in after.objects:
        before_obj = before_by_id.get(after_obj.id)
        if before_obj is None:
            changes.append(
                {
                    "object_id": after_obj.id,
                    "change_type": "object_added",
                    "added_action_ids": [action.action_id for action in after_obj.actions],
                    "changed_attributes": after_obj.attributes,
                }
            )
            continue

        before_action_ids = {action.action_id for action in before_obj.actions}
        added_action_ids = [
            action.action_id
            for action in after_obj.actions
            if action.action_id not in before_action_ids
        ]
        changed_attributes = {
            key: {"before": before_obj.attributes.get(key), "after": after_obj.attributes.get(key)}
            for key in sorted(set(before_obj.attributes) | set(after_obj.attributes))
            if before_obj.attributes.get(key) != after_obj.attributes.get(key)
        }
        if added_action_ids or changed_attributes:
            changes.append(
                {
                    "object_id": after_obj.id,
                    "change_type": "object_updated",
                    "added_action_ids": added_action_ids,
                    "changed_attributes": changed_attributes,
                }
            )

    return {
        "changed_object_count": len(changes),
        "changes": changes,
    }
