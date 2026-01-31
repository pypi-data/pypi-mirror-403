"""
XP Calculation Utilities.

Ported from playcademy packages/timeback so SDK users get consistent,
mastery-based XP behavior.

XP is calculated from duration, accuracy, and attempt number:

    base_xp = duration_minutes
    xp = base_xp * accuracy_multiplier * attempt_multiplier

- Mastery threshold: 80% accuracy required to earn any XP.
- Perfect bonus: ~100% accuracy earns 1.25x multiplier (floating-point safe).
- Diminishing returns: attempt 1 = 1.0x, 2 = 0.5x, 3 = 0.25x, 4+ = 0x.
"""

from __future__ import annotations

import math

from .constants import PERFECT_ACCURACY_THRESHOLD


def _get_attempt_multiplier(attempt_number: int) -> float:
    """
    Get the attempt multiplier for diminishing returns on re-attempts.

    - 1st attempt: 1.0x (full XP)
    - 2nd attempt: 0.5x
    - 3rd attempt: 0.25x
    - 4th+ attempt: 0x

    Args:
        attempt_number: Which attempt this is (1-based)

    Returns:
        Attempt multiplier
    """
    if attempt_number == 1:
        return 1.0
    if attempt_number == 2:
        return 0.5
    if attempt_number == 3:
        return 0.25
    return 0.0


def _get_accuracy_multiplier(accuracy: float) -> float:
    """
    Get the accuracy multiplier based on performance.

    Requires 80% accuracy (mastery threshold) to earn any XP.

    - 100% accuracy (or very close): 1.25x (bonus for perfect)
    - 80-99% accuracy: 1.0x (full XP for mastery)
    - < 80% accuracy: 0x (no XP, mastery not demonstrated)

    Args:
        accuracy: Accuracy as decimal (0-1)

    Returns:
        Accuracy multiplier
    """
    if not math.isfinite(accuracy) or accuracy < 0:
        return 0.0

    if accuracy >= PERFECT_ACCURACY_THRESHOLD:
        return 1.25

    if accuracy >= 0.8:
        return 1.0

    return 0.0


def calculate_xp(duration_seconds: float, accuracy: float, attempt_number: int) -> float:
    """
    Calculate XP based on duration, accuracy, and attempt number.

    Args:
        duration_seconds: Total session duration in seconds
        accuracy: Accuracy as decimal (0-1)
        attempt_number: Which attempt this is (1 = first, 2 = first re-attempt, etc.)

    Returns:
        Calculated XP, rounded to nearest tenth
    """
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        return 0.0

    duration_minutes = duration_seconds / 60
    base_xp = duration_minutes

    accuracy_multiplier = _get_accuracy_multiplier(accuracy)
    attempt_multiplier = _get_attempt_multiplier(attempt_number)

    # Round to nearest tenth (e.g., 4.123 -> 4.1)
    # Use floor(x + 0.5) instead of round() to match JavaScript's Math.round() behavior
    # (Python's round() uses banker's rounding which rounds 0.5 to nearest even)
    raw = base_xp * accuracy_multiplier * attempt_multiplier * 10
    return math.floor(raw + 0.5) / 10
