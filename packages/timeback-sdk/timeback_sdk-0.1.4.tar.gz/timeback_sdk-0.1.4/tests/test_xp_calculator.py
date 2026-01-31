"""Tests for XP calculator."""

from __future__ import annotations

import math

from timeback.shared.xp_calculator import calculate_xp

# Base rate: 1 minute = 1 XP (before multipliers)
TEN_MINUTES_IN_SECONDS = 600


class TestFloatingPointEdgeCases:
    """Test floating point accuracy edge cases."""

    def test_accuracy_very_close_to_1_gets_bonus(self) -> None:
        """Accuracy ~1.0 should get bonus (handles floating point precision)."""
        # Simulates 10/10 = 0.9999999999999999 due to floating point
        almost_perfect = 0.9999999999999999
        xp = calculate_xp(TEN_MINUTES_IN_SECONDS, almost_perfect, 1)
        assert xp == 12.5

    def test_accuracy_at_exactly_0_8_boundary_gets_full_xp(self) -> None:
        """Accuracy at exactly 0.8 should get full XP."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.8, 1) == 10

    def test_accuracy_just_below_0_8_gets_0_xp(self) -> None:
        """Accuracy just below 0.8 should get 0 XP."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.79999999999, 1) == 0

    def test_calculated_accuracy_8_out_of_10(self) -> None:
        """Calculated accuracy like 8/10 should work correctly."""
        accuracy = 8 / 10
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, accuracy, 1) == 10

    def test_calculated_accuracy_10_out_of_10_gets_bonus(self) -> None:
        """Calculated accuracy like 10/10 should get bonus."""
        accuracy = 10 / 10
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, accuracy, 1) == 12.5


class TestInvalidInputHandling:
    """Test invalid input handling."""

    def test_negative_duration_returns_0(self) -> None:
        """Negative duration should return 0."""
        xp = calculate_xp(-600, 1.0, 1)
        assert xp >= 0
        assert xp == 0

    def test_accuracy_greater_than_1_treated_as_perfect(self) -> None:
        """Accuracy > 1.0 is treated as perfect."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.5, 1) == 12.5

    def test_negative_accuracy_returns_0_xp(self) -> None:
        """Negative accuracy should return 0 XP."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, -0.5, 1) == 0

    def test_attempt_number_0_returns_0_xp(self) -> None:
        """Attempt number 0 should return 0 XP."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 0) == 0

    def test_negative_attempt_number_returns_0_xp(self) -> None:
        """Negative attempt number should return 0 XP."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, -1) == 0

    def test_nan_duration_returns_0(self) -> None:
        """NaN duration should return 0."""
        xp = calculate_xp(float("nan"), 1.0, 1)
        assert not math.isnan(xp)
        assert xp == 0

    def test_nan_accuracy_returns_0(self) -> None:
        """NaN accuracy should return 0."""
        xp = calculate_xp(TEN_MINUTES_IN_SECONDS, float("nan"), 1)
        assert not math.isnan(xp)
        assert xp == 0

    def test_infinity_duration_returns_finite_value(self) -> None:
        """Infinity duration returns finite value (0)."""
        xp = calculate_xp(float("inf"), 1.0, 1)
        assert math.isfinite(xp)
        assert xp == 0


class TestAccuracyMultipliers:
    """Test accuracy multipliers (mastery-based, 80% threshold)."""

    def test_100_percent_accuracy_gives_1_25x_bonus(self) -> None:
        """100% accuracy gives 1.25x bonus."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 1) == 12.5

    def test_80_to_99_percent_accuracy_gives_1x(self) -> None:
        """80-99% accuracy gives 1.0x."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.99, 1) == 10
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.9, 1) == 10
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.8, 1) == 10

    def test_less_than_80_percent_accuracy_gives_0x(self) -> None:
        """< 80% accuracy gives 0x."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.79, 1) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.65, 1) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.5, 1) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0, 1) == 0


class TestAttemptMultipliers:
    """Test attempt multipliers (diminishing returns)."""

    def test_1st_attempt_gives_full_xp(self) -> None:
        """1st attempt gives full XP (1.0x)."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 1) == 12.5

    def test_2nd_attempt_gives_0_5x(self) -> None:
        """2nd attempt gives 0.5x."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 2) == 6.3

    def test_3rd_attempt_gives_0_25x(self) -> None:
        """3rd attempt gives 0.25x."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 3) == 3.1

    def test_4th_plus_attempts_give_0x(self) -> None:
        """4th+ attempts give 0x."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 4) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 10) == 0


class TestCombinedMultipliers:
    """Test combined accuracy and attempt multipliers."""

    def test_80_percent_accuracy_on_2nd_attempt(self) -> None:
        """80% accuracy on 2nd attempt."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.8, 2) == 5

    def test_100_percent_accuracy_on_3rd_attempt(self) -> None:
        """100% accuracy on 3rd attempt."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 1.0, 3) == 3.1

    def test_less_than_80_percent_accuracy_always_gives_0(self) -> None:
        """< 80% accuracy always gives 0 regardless of attempt."""
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.7, 1) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.7, 2) == 0
        assert calculate_xp(TEN_MINUTES_IN_SECONDS, 0.7, 3) == 0


class TestDurationScaling:
    """Test duration scaling."""

    def test_base_rate_is_1_xp_per_minute(self) -> None:
        """Base rate is 1 XP per minute."""
        assert calculate_xp(60, 0.8, 1) == 1

    def test_scales_linearly_with_duration(self) -> None:
        """Scales linearly with duration."""
        assert calculate_xp(300, 1.0, 1) == 6.3  # 5 * 1.25 = 6.25 -> 6.3
        assert calculate_xp(30, 1.0, 1) == 0.6  # 0.5 * 1.25 = 0.625 -> 0.6

    def test_handles_zero_duration(self) -> None:
        """Handles zero duration."""
        assert calculate_xp(0, 1.0, 1) == 0


class TestRounding:
    """Test rounding behavior."""

    def test_rounds_to_nearest_tenth(self) -> None:
        """Rounds to nearest tenth."""
        assert calculate_xp(420, 1.0, 1) == 8.8  # 7 * 1.25 = 8.75 -> 8.8
        assert calculate_xp(180, 1.0, 2) == 1.9  # 3 * 1.25 * 0.5 = 1.875 -> 1.9
