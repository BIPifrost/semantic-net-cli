"""Apply control execution feedback to semantic twin graphs."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.models.control import ControlExecutionRecord, PropagatedControlEffect
from semantic_net_cli.models.twin import SemanticTwinGraph, SemanticTwinObject, TwinAction


def apply_control_feedback_to_twin_graph(
    graph: SemanticTwinGraph,
    record: ControlExecutionRecord,
    effect: PropagatedControlEffect | None = None,
) -> SemanticTwinGraph:
    """Return a new graph where target objects contain the control execution record."""

    updated_objects: list[SemanticTwinObject] = []
    target_ids = set(record.target_object_ids)
    updates_by_object = _group_metric_updates(effect)
    affected_ids = target_ids | set(updates_by_object)

    for item in graph.objects:
        if item.id not in affected_ids:
            updated_objects.append(item.model_copy(deep=True))
            continue

        item_copy = item.model_copy(deep=True)
        attributes = dict(item_copy.attributes)
        metric_updates = updates_by_object.get(item.id, [])
        if metric_updates:
            metrics = dict(attributes.get("metrics", {}))
            for update in metric_updates:
                metrics[update.metric_name] = update.after
            attributes["metrics"] = metrics
        attributes["control_feedback"] = {
            "last_execution_id": record.execution_id,
            "last_execution_status": record.status,
            "last_feedback_summary": record.feedback_summary,
            "metric_observations": [
                observation.model_dump()
                for observation in record.metric_observations
                if observation.object_id == item.id
            ],
            "effect_id": effect.effect_id if effect else None,
            "propagation_mode": effect.mode if effect else None,
            "propagation_summary": effect.propagation_summary if effect else None,
            "metric_updates": [update.model_dump() for update in metric_updates],
        }
        actions = list(item_copy.actions)
        if item.id in target_ids:
            actions.append(
                TwinAction(
                    action_id=record.execution_id,
                    action_type="control_execution",
                    status=record.status,
                    reason=", ".join(record.applied_actions) or "no applied action",
                    result=record.feedback_summary,
                    source_action_id=record.source_action_id,
                    executor=record.executor,
                    confidence=record.confidence,
                )
            )
        updated_objects.append(
            item_copy.model_copy(
                deep=True,
                update={"attributes": attributes, "actions": actions},
            )
        )

    return SemanticTwinGraph(objects=updated_objects)


def build_history_context_from_twin_graph(graph: SemanticTwinGraph) -> dict[str, Any]:
    """Build compact history_context from semantic twin actions for the next workflow round."""

    recent_actions: list[dict[str, Any]] = []
    for item in graph.objects:
        for action in item.actions:
            payload = action.model_dump()
            payload["object_id"] = item.id
            recent_actions.append(payload)

    return {
        "action_count": len(recent_actions),
        "recent_actions": recent_actions[-20:],
    }


def _group_metric_updates(effect: PropagatedControlEffect | None) -> dict[str, list]:
    if effect is None:
        return {}
    grouped: dict[str, list] = {}
    for update in effect.metric_updates:
        grouped.setdefault(update.object_id, []).append(update)
    return grouped
