"""Deterministic relation-aware control effect propagation."""

from __future__ import annotations

from semantic_net_cli.models.control import (
    ControlExecutionRecord,
    MetricUpdate,
    PropagatedControlEffect,
)
from semantic_net_cli.models.twin import SemanticTwinGraph, SemanticTwinObject


WIRELESS_CHANNEL_EFFECTS = {
    "loss_rate": -0.18,
    "retransmission_rate": -0.15,
    "avg_snr_db": 0.10,
    "throughput_mbps": 0.08,
    "delay_ms": -0.10,
    "utilization": -0.06,
}

TRAFFIC_REBALANCE_EFFECTS = {
    "utilization": -0.12,
    "queue_length": -0.18,
    "delay_ms": -0.08,
    "throughput_mbps": 0.05,
}

RELATED_INTERFACE_EFFECTS = {
    "snr_db": 0.08,
    "error_packets": -0.12,
}

METRIC_BOUNDS = {
    "loss_rate": (0.0, 1.0),
    "retransmission_rate": (0.0, 1.0),
    "utilization": (0.0, 1.0),
    "throughput_mbps": (0.0, None),
    "delay_ms": (0.0, None),
    "queue_length": (0.0, None),
    "avg_snr_db": (0.0, None),
    "snr_db": (0.0, None),
    "error_packets": (0.0, None),
}


class ControlEffectPropagator:
    """Apply conservative metric coupling from a simulated control action."""

    def propagate(
        self,
        *,
        graph: SemanticTwinGraph,
        record: ControlExecutionRecord,
        mode: str,
        damping_factor: float,
    ) -> PropagatedControlEffect:
        updates: list[MetricUpdate] = []
        by_id = graph.by_id

        for target_id in record.target_object_ids:
            target = by_id.get(target_id)
            if target is None:
                continue
            updates.extend(
                _build_updates_for_object(
                    target,
                    _select_effects(record, target),
                    damping_factor,
                    "direct action effect",
                )
            )
            for related in _related_objects(graph, target):
                updates.extend(
                    _build_updates_for_object(
                        related,
                        RELATED_INTERFACE_EFFECTS,
                        damping_factor * 0.5,
                        f"relation propagation from {target.id}",
                    )
                )

        changed_object_ids = sorted({item.object_id for item in updates})
        return PropagatedControlEffect(
            effect_id=f"effect-{record.execution_id}",
            source_execution_id=record.execution_id,
            mode=mode,
            changed_object_ids=changed_object_ids,
            metric_updates=updates,
            propagation_summary=(
                f"Applied {mode} control effect propagation with damping_factor={damping_factor}."
            ),
        )


def _select_effects(record: ControlExecutionRecord, target: SemanticTwinObject) -> dict[str, float]:
    action_text = " ".join([*record.applied_actions, record.feedback_summary]).lower()
    if "wireless" in action_text or "channel" in action_text or target.type.startswith("channel:wifi"):
        return WIRELESS_CHANNEL_EFFECTS
    if "traffic" in action_text or "rate-limit" in action_text or "redistribution" in action_text:
        return TRAFFIC_REBALANCE_EFFECTS
    return TRAFFIC_REBALANCE_EFFECTS


def _related_objects(graph: SemanticTwinGraph, target: SemanticTwinObject) -> list[SemanticTwinObject]:
    by_id = graph.by_id
    related_ids: set[str] = set()
    connects = target.relations.get("connects", [])
    if isinstance(connects, list):
        related_ids.update(str(item) for item in connects)
    connected_by = target.relations.get("connected_by", [])
    if isinstance(connected_by, list):
        related_ids.update(str(item) for item in connected_by)
    return [by_id[item_id] for item_id in sorted(related_ids) if item_id in by_id]


def _build_updates_for_object(
    obj: SemanticTwinObject,
    effects: dict[str, float],
    damping_factor: float,
    reason: str,
) -> list[MetricUpdate]:
    metrics = obj.attributes.get("metrics", {})
    if not isinstance(metrics, dict):
        return []
    updates: list[MetricUpdate] = []
    for metric_name, relative_delta in effects.items():
        if metric_name not in metrics:
            continue
        before = metrics[metric_name]
        if not isinstance(before, int | float):
            continue
        after = _bounded_value(metric_name, before * (1.0 + relative_delta * damping_factor))
        if after != before:
            updates.append(
                MetricUpdate(
                    object_id=obj.id,
                    metric_name=metric_name,
                    before=before,
                    after=after,
                    reason=reason,
                )
            )
    return updates


def _bounded_value(metric_name: str, value: float) -> float:
    lower, upper = METRIC_BOUNDS.get(metric_name, (None, None))
    if lower is not None:
        value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return round(value, 6)
