"""Closed-loop stability monitoring for simulated control feedback."""

from __future__ import annotations

from semantic_net_cli.models.control import StabilityAssessment


class StabilityMonitor:
    """Track loop signatures and classify convergence or oscillation."""

    def __init__(self, stable_window: int = 2, damping_factor: float = 0.5) -> None:
        self.stable_window = stable_window
        self.damping_factor = damping_factor
        self.signatures: list[str] = []
        self.oscillation_count = 0
        self.normal_streak = 0

    def assess(
        self,
        iteration: int,
        network_status: str,
        primary_cause: str,
        recommended_action: str,
        target_object_ids: list[str],
        changed_object_count: int,
    ) -> StabilityAssessment:
        signature = _signature(
            network_status,
            primary_cause,
            recommended_action,
            target_object_ids,
        )
        self.signatures.append(signature)

        if network_status == "normal" and changed_object_count == 0:
            self.normal_streak += 1
        else:
            self.normal_streak = 0

        if self.normal_streak >= self.stable_window:
            return StabilityAssessment(
                iteration=iteration,
                stability="stable",
                terminal_reason="stable_state_reached",
                should_stop=True,
                damping_factor=1.0,
                oscillation_count=self.oscillation_count,
                signature=signature,
                rationale="Stable normal state persisted for the configured window.",
            )

        if _has_abab_pattern(self.signatures):
            self.oscillation_count += 1
            if self.oscillation_count > 1:
                return StabilityAssessment(
                    iteration=iteration,
                    stability="oscillating",
                    terminal_reason="oscillation_persisted_after_damping",
                    should_stop=True,
                    damping_factor=self.damping_factor,
                    oscillation_count=self.oscillation_count,
                    signature=signature,
                    rationale="Repeated A-B-A-B pattern persisted after damped mode.",
                )
            return StabilityAssessment(
                iteration=iteration,
                stability="damped",
                terminal_reason=None,
                should_stop=False,
                damping_factor=self.damping_factor,
                oscillation_count=self.oscillation_count,
                signature=signature,
                rationale="A-B-A-B pattern detected; entering damped mode.",
            )

        return StabilityAssessment(
            iteration=iteration,
            stability="improving",
            terminal_reason=None,
            should_stop=False,
            damping_factor=1.0,
            oscillation_count=self.oscillation_count,
            signature=signature,
            rationale="No stable terminal state or oscillation pattern detected.",
        )


def _signature(
    network_status: str,
    primary_cause: str,
    recommended_action: str,
    target_object_ids: list[str],
) -> str:
    targets = ",".join(sorted(target_object_ids)) or "none"
    return f"{network_status}|{primary_cause}|{recommended_action}|{targets}"


def _has_abab_pattern(signatures: list[str]) -> bool:
    if len(signatures) < 4:
        return False
    a, b, c, d = signatures[-4:]
    return a == c and b == d and a != b
