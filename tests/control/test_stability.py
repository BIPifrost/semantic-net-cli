from semantic_net_cli.control.stability import StabilityMonitor


def test_stability_monitor_marks_first_iteration_improving() -> None:
    monitor = StabilityMonitor(stable_window=2)

    assessment = monitor.assess(
        iteration=1,
        network_status="degraded",
        primary_cause="wireless_A",
        recommended_action="shift_to_B",
        target_object_ids=["channel_B"],
        changed_object_count=2,
    )

    assert assessment.stability == "improving"
    assert assessment.should_stop is False
    assert assessment.damping_factor == 1.0


def test_stability_monitor_enters_damped_mode_for_abab_pattern() -> None:
    monitor = StabilityMonitor(stable_window=2)

    monitor.assess(1, "degraded", "wireless_A", "shift_to_B", ["B"], 2)
    monitor.assess(2, "degraded", "wireless_B", "shift_to_A", ["A"], 2)
    monitor.assess(3, "degraded", "wireless_A", "shift_to_B", ["B"], 2)
    assessment = monitor.assess(4, "degraded", "wireless_B", "shift_to_A", ["A"], 2)

    assert assessment.stability == "damped"
    assert assessment.should_stop is False
    assert assessment.damping_factor == 0.5
    assert assessment.oscillation_count == 1


def test_stability_monitor_stops_if_damping_does_not_break_oscillation() -> None:
    monitor = StabilityMonitor(stable_window=2)

    monitor.assess(1, "degraded", "wireless_A", "shift_to_B", ["B"], 2)
    monitor.assess(2, "degraded", "wireless_B", "shift_to_A", ["A"], 2)
    monitor.assess(3, "degraded", "wireless_A", "shift_to_B", ["B"], 2)
    monitor.assess(4, "degraded", "wireless_B", "shift_to_A", ["A"], 2)
    monitor.assess(5, "degraded", "wireless_A", "shift_to_B", ["B"], 2)
    assessment = monitor.assess(6, "degraded", "wireless_B", "shift_to_A", ["A"], 2)

    assert assessment.stability == "oscillating"
    assert assessment.should_stop is True
    assert assessment.terminal_reason == "oscillation_persisted_after_damping"


def test_stability_monitor_stops_after_stable_window() -> None:
    monitor = StabilityMonitor(stable_window=2)

    monitor.assess(1, "normal", "none", "no further action", [], 0)
    assessment = monitor.assess(2, "normal", "none", "no further action", [], 0)

    assert assessment.stability == "stable"
    assert assessment.should_stop is True
    assert assessment.terminal_reason == "stable_state_reached"
