"""Capability-alignment tradeoff: raw measurements only. No single formula is asserted
as "the" research metric — analysis scripts combine these as needed.
"""
from __future__ import annotations


def alignment_gain(condition_alignment: float, baseline_alignment: float) -> float:
    return condition_alignment - baseline_alignment


def capability_change(condition_performance: float, baseline_performance: float) -> float:
    return condition_performance - baseline_performance


def relative_capability_retention(condition_performance: float, baseline_performance: float) -> float | None:
    """None (not 0, not 1, not inf) when baseline performance is zero — that ratio is
    undefined, not a special case to paper over."""
    if baseline_performance == 0:
        return None
    return condition_performance / baseline_performance


def alignment_per_capability_loss(alignment_gain_value: float, capability_change_value: float) -> float | None:
    """Alignment gained per unit of capability lost. Only defined when capability
    actually decreased (capability_change_value < 0); returns None otherwise rather than
    a misleading value (e.g. a negative "loss" or division by zero)."""
    if capability_change_value >= 0:
        return None
    return alignment_gain_value / abs(capability_change_value)
