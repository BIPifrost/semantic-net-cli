"""Deterministic simulated control executor for the CLI prototype."""

from __future__ import annotations

from typing import Any

from semantic_net_cli.models.control import ControlExecutionRecord, MetricObservation
from semantic_net_cli.models.task_outputs import OptimizationAction
from semantic_net_cli.models.twin import SemanticTwinGraph


class SimulatedControlExecutor:
    """Convert U_k into a reproducible execution record without touching real devices."""

    name = "simulated_control_executor"

    def execute(
        self,
        action: OptimizationAction,
        graph: SemanticTwinGraph,
        mode: str = "normal",
    ) -> ControlExecutionRecord:
        target_ids = list(action.target_object_ids)
        applied_actions = list(action.candidate_actions) or [action.recommended_action]
        status = "skipped" if not target_ids else "damped" if mode == "damped" else "succeeded"
        observations = self._build_metric_observations(target_ids, graph)
        target_summary = ", ".join(target_ids) if target_ids else "no target objects"

        return ControlExecutionRecord(
            execution_id=f"exec-{action.action_id}",
            source_action_id=action.action_id,
            executor=self.name,
            status=status,
            target_object_ids=target_ids,
            applied_actions=applied_actions,
            feedback_summary=(
                f"Simulated execution {status} for {target_summary}; "
                f"recommended_action={action.recommended_action}"
            ),
            metric_observations=observations,
            confidence=action.confidence,
        )

    def _build_metric_observations(
        self,
        target_ids: list[str],
        graph: SemanticTwinGraph,
    ) -> list[MetricObservation]:
        observations: list[MetricObservation] = []
        by_id = graph.by_id
        for target_id in target_ids:
            target = by_id.get(target_id)
            if target is None:
                continue
            metrics = target.attributes.get("metrics", {})
            if not isinstance(metrics, dict):
                continue
            for metric_name in ("loss_rate", "utilization", "delay_ms", "queue_length"):
                if metric_name not in metrics:
                    continue
                before = metrics[metric_name]
                observations.append(
                    MetricObservation(
                        object_id=target_id,
                        metric_name=metric_name,
                        before=before,
                        after=_simulate_improved_value(metric_name, before),
                    )
                )
        return observations


def _simulate_improved_value(metric_name: str, before: Any) -> Any:
    if not isinstance(before, int | float):
        return before
    if metric_name in {"loss_rate", "utilization"}:
        return round(max(0.0, before * 0.8), 6)
    if metric_name in {"delay_ms", "queue_length"}:
        return round(max(0.0, before * 0.9), 6)
    return before
