"""Tests for activity progress computation (pctComplete) using EduBridge analytics."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from timeback.server.handlers.activity import (
    compute_progress,
    resolve_total_lessons,
)
from timeback_common import APIError

# ─────────────────────────────────────────────────────────────────────────────
# Test: resolve_total_lessons
# ─────────────────────────────────────────────────────────────────────────────


class TestResolveTotalLessons:
    """Tests for resolve_total_lessons function."""

    def test_returns_total_lessons_from_base_metadata(self) -> None:
        """Should return totalLessons from base metadata."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "metadata": {"metrics": {"totalLessons": 100}},
        }
        result = resolve_total_lessons(course_config, "staging")
        assert result == 100

    def test_returns_total_lessons_from_env_override(self) -> None:
        """Should prefer totalLessons from env-specific override."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "metadata": {"metrics": {"totalLessons": 100}},
            "overrides": {"staging": {"metadata": {"metrics": {"totalLessons": 200}}}},
        }
        result = resolve_total_lessons(course_config, "staging")
        assert result == 200

    def test_falls_back_to_base_when_override_missing(self) -> None:
        """Should fall back to base when env override doesn't have totalLessons."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "metadata": {"metrics": {"totalLessons": 100}},
            "overrides": {"staging": {"metadata": {"metrics": {}}}},
        }
        result = resolve_total_lessons(course_config, "staging")
        assert result == 100

    def test_maps_local_env_to_staging(self) -> None:
        """Should map 'local' env to 'staging' for override lookup."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "metadata": {"metrics": {"totalLessons": 100}},
            "overrides": {"staging": {"metadata": {"metrics": {"totalLessons": 200}}}},
        }
        result = resolve_total_lessons(course_config, "local")
        assert result == 200

    def test_returns_none_when_not_configured(self) -> None:
        """Should return None when totalLessons is not configured."""
        course_config = {"subject": "Math", "grade": 3}
        result = resolve_total_lessons(course_config, "staging")
        assert result is None

    def test_returns_none_when_metadata_empty(self) -> None:
        """Should return None when metadata exists but metrics don't."""
        course_config = {"subject": "Math", "grade": 3, "metadata": {}}
        result = resolve_total_lessons(course_config, "staging")
        assert result is None

    def test_handles_float_total_lessons(self) -> None:
        """Should convert float totalLessons to int."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "metadata": {"metrics": {"totalLessons": 99.9}},
        }
        result = resolve_total_lessons(course_config, "staging")
        assert result == 99


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Gating Conditions
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressGating:
    """Tests for compute_progress gating conditions."""

    @pytest.mark.asyncio
    async def test_returns_none_when_pct_complete_already_provided(self) -> None:
        """Should return None when client already provided pctComplete."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"pctComplete": 50, "metrics": {"masteredUnits": 10}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result is None
        # Should not have called EduBridge
        mock_client.edubridge.enrollments.list.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_mastered_units_missing(self) -> None:
        """Should return None when masteredUnits is not in payload."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"totalQuestions": 10}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result is None
        mock_client.edubridge.enrollments.list.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_mastered_units_is_zero(self) -> None:
        """Should return None when masteredUnits is 0."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 0}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result is None
        mock_client.edubridge.enrollments.list.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_mastered_units_is_negative(self) -> None:
        """Should return None when masteredUnits is negative."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": -5}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_total_lessons_not_configured(self) -> None:
        """Should return None when totalLessons is not configured."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 10}},
            course_config={"subject": "Math", "grade": 3},  # No totalLessons
            env="staging",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_total_lessons_is_zero(self) -> None:
        """Should return None when totalLessons is 0."""
        mock_client = MagicMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 10}},
            course_config={"metadata": {"metrics": {"totalLessons": 0}}},
            env="staging",
        )

        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Mock helpers for EduBridge
# ─────────────────────────────────────────────────────────────────────────────


def create_mock_enrollment(enrollment_id: str, course_id: str) -> Any:
    """Create a mock enrollment object."""
    enrollment = MagicMock()
    enrollment.id = enrollment_id
    enrollment.course = MagicMock()
    enrollment.course.id = course_id
    return enrollment


def create_mock_facts(mastered_units: int) -> dict[str, dict[str, Any]]:
    """Create mock enrollment facts with activity metrics.

    Returns data in the DailyActivityMap format expected by aggregate_activity_metrics.
    """
    from timeback_edubridge.types.analytics import (
        ActivityMetricsData,
        SubjectMetrics,
        TimeSpentMetricsData,
    )

    subject_metrics = SubjectMetrics(
        activity_metrics=ActivityMetricsData(
            xp_earned=100.0,
            total_questions=20,
            correct_questions=15,
            mastered_units=mastered_units,
        ),
        time_spent_metrics=TimeSpentMetricsData(
            active_seconds=300,
            inactive_seconds=60,
            waste_seconds=10,
        ),
        apps=["TestApp"],
    )

    return {
        "2024-03-15": {
            "Math": subject_metrics,
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Computation Logic
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressComputation:
    """Tests for compute_progress computation logic using EduBridge."""

    @pytest.mark.asyncio
    async def test_computes_pct_from_current_mastered_units_only(self) -> None:
        """Should compute pct when no historical results exist."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 10}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result == 10  # 10/100 * 100 = 10

    @pytest.mark.asyncio
    async def test_sums_historical_and_current_mastered_units(self) -> None:
        """Should sum historical masteredUnits with current submission."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        # Mock facts with 15 historical mastered units
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(15)
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 15}},  # Current = 15
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (15) + current (15) = 30, 30/100 = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_returns_none_when_enrollment_not_found(self) -> None:
        """Should return None when enrollment is not found for the student/course."""
        mock_client = MagicMock()
        # Return enrollments for a different course
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "different-course")]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 10}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Rounding and Clamping
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressRounding:
    """Tests for compute_progress rounding and clamping."""

    @pytest.mark.asyncio
    async def test_rounds_one_third_to_33(self) -> None:
        """Should round 1/3 (33.33...) to 33."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 1}},
            course_config={"metadata": {"metrics": {"totalLessons": 3}}},
            env="staging",
        )

        assert result == 33

    @pytest.mark.asyncio
    async def test_rounds_two_thirds_to_67(self) -> None:
        """Should round 2/3 (66.67) to 67."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 2}},
            course_config={"metadata": {"metrics": {"totalLessons": 3}}},
            env="staging",
        )

        assert result == 67

    @pytest.mark.asyncio
    async def test_clamps_to_100_when_exceeds(self) -> None:
        """Should clamp to 100 when total exceeds totalLessons."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        # Historical = 80
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(80)
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 50}},  # 80 + 50 = 130
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result == 100

    @pytest.mark.asyncio
    async def test_returns_100_when_exactly_complete(self) -> None:
        """Should return 100 when exactly at totalLessons."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={"metrics": {"masteredUnits": 100}},
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        assert result == 100


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Error Handling
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressErrorHandling:
    """Tests for compute_progress error handling.

    IMPORTANT: Only TimebackError (and subclasses like APIError) should be caught.
    Other exceptions (like pydantic.ValidationError) indicate SDK bugs and MUST propagate.
    """

    @pytest.mark.asyncio
    async def test_catches_api_error_on_enrollments_and_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """TimebackError on enrollments.list should be caught, logged as warning, return None."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            side_effect=APIError("Service unavailable", status_code=503)
        )

        with caplog.at_level("WARNING"):
            result = await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={"metrics": {"masteredUnits": 10}},
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        assert result is None
        assert "Failed to fetch enrollments" in caplog.text
        assert "course-123" in caplog.text

    @pytest.mark.asyncio
    async def test_catches_api_error_on_facts_and_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """TimebackError on get_enrollment_facts should be caught, logged as warning, return None."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            side_effect=APIError("Internal server error", status_code=500)
        )

        with caplog.at_level("WARNING"):
            result = await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={"metrics": {"masteredUnits": 10}},
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        assert result is None
        assert "Failed to fetch enrollment facts" in caplog.text
        assert "enrollment-1" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_error_and_propagates_non_timeback_error_on_enrollments(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-TimebackError exceptions should be logged at ERROR level, then re-raised."""
        from pydantic import ValidationError as PydanticValidationError

        mock_client = MagicMock()
        # Simulate a Pydantic ValidationError - this is an SDK bug, not an API failure
        mock_client.edubridge.enrollments.list = AsyncMock(
            side_effect=PydanticValidationError.from_exception_data(
                "Enrollment",
                [
                    {
                        "type": "int_from_float",
                        "loc": ("activeSeconds",),
                        "msg": "Input should be a valid integer",
                        "input": 342.64,
                    }
                ],
            )
        )

        with caplog.at_level("ERROR"), pytest.raises(PydanticValidationError):
            await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={"metrics": {"masteredUnits": 10}},
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        # Verify error was logged with context before re-raising
        assert "Unexpected error fetching enrollments" in caplog.text
        assert "course-123" in caplog.text
        assert "student-456" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_error_and_propagates_non_timeback_error_on_facts(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-TimebackError on get_enrollment_facts should be logged at ERROR, then re-raised."""
        from pydantic import ValidationError as PydanticValidationError

        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        # Simulate SDK bug during parsing
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            side_effect=PydanticValidationError.from_exception_data(
                "SubjectMetrics",
                [
                    {
                        "type": "int_from_float",
                        "loc": ("timeSpentMetrics", "activeSeconds"),
                        "msg": "Input should be a valid integer, got float",
                        "input": 342.64,
                    }
                ],
            )
        )

        with caplog.at_level("ERROR"), pytest.raises(PydanticValidationError):
            await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={"metrics": {"masteredUnits": 10}},
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        # Verify error was logged with context before re-raising
        assert "Unexpected error fetching enrollment facts" in caplog.text
        assert "course-123" in caplog.text
        assert "enrollment-1" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_error_and_propagates_generic_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Generic Exception should be logged at ERROR level, then re-raised."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            side_effect=RuntimeError("Unexpected internal error")
        )

        with (
            caplog.at_level("ERROR"),
            pytest.raises(RuntimeError, match="Unexpected internal error"),
        ):
            await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={"metrics": {"masteredUnits": 10}},
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        # Verify error was logged before re-raising
        assert "Unexpected error fetching enrollments" in caplog.text
        assert "Unexpected internal error" in caplog.text


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Float masteredUnits
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressFloatMasteredUnits:
    """Tests for compute_progress with float masteredUnits values."""

    @pytest.mark.asyncio
    async def test_handles_float_mastered_units(self) -> None:
        """Should convert float masteredUnits to int."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(return_value=[])

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-1",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10.7},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # 10.7 truncated to 10
        assert result == 10


# ─────────────────────────────────────────────────────────────────────────────
# Mock helpers for Weekly Facts
# ─────────────────────────────────────────────────────────────────────────────


def create_mock_weekly_fact(
    activity_id: str,
    enrollment_id: str | None = None,
    course_id: str | None = None,
) -> MagicMock:
    """Create a mock weekly fact object."""
    fact = MagicMock()
    fact.activity_id = activity_id
    fact.enrollment_id = enrollment_id
    fact.course_id = course_id
    return fact


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress - Retry Safety / Idempotency
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeProgressRetrySafety:
    """Tests for compute_progress retry-safety / idempotency logic.

    On retries, EduBridge enrollment facts may already include this activity's
    metrics. We detect this via weekly facts to avoid double-counting.
    """

    @pytest.mark.asyncio
    async def test_includes_current_mastered_when_not_already_processed(self) -> None:
        """Should include current masteredUnits when activity is not in weekly facts."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)  # Historical = 20
        )
        # Weekly facts contains different activity
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[create_mock_weekly_fact("different-activity", "enrollment-1")]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (20) + current (10) = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_skips_current_mastered_when_already_processed_by_enrollment(
        self,
    ) -> None:
        """Should skip current masteredUnits when activity already processed (matched by enrollment)."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(30)  # Already includes current activity
        )
        # Weekly facts shows this activity was already processed for this enrollment
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[create_mock_weekly_fact("activity-abc", "enrollment-1", None)]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Only historical (30), current NOT added = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_skips_current_mastered_when_already_processed_by_course(self) -> None:
        """Should skip current masteredUnits when activity already processed (matched by course)."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(30)  # Already includes current activity
        )
        # Weekly facts shows this activity was already processed for this course
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[create_mock_weekly_fact("activity-abc", None, "course-123")]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Only historical (30), current NOT added = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_includes_current_when_activity_id_matches_but_context_differs(
        self,
    ) -> None:
        """Should include current masteredUnits when activityId matches but enrollment/course differ."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Same activity ID but for different enrollment/course
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[
                create_mock_weekly_fact("activity-abc", "different-enrollment", "different-course")
            ]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (20) + current (10) = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_skips_current_on_weekly_facts_api_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should conservatively skip current masteredUnits when weekly facts API fails."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Weekly facts API fails
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            side_effect=APIError("Service unavailable", status_code=503)
        )

        with caplog.at_level("WARNING"):
            result = await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={
                    "id": "activity-abc",
                    "endedAt": "2024-03-15",
                    "metrics": {"masteredUnits": 10},
                },
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        # Conservative: only historical (20), assume already processed
        assert result == 20
        assert "Failed to fetch weekly facts" in caplog.text
        assert "assuming already processed" in caplog.text

    @pytest.mark.asyncio
    async def test_skips_current_on_weekly_facts_unexpected_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should conservatively skip current masteredUnits on unexpected weekly facts error."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Unexpected error (e.g. SDK bug, parsing issue)
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            side_effect=RuntimeError("Parsing failed")
        )

        with caplog.at_level("WARNING"):
            result = await compute_progress(
                client=mock_client,
                course_id="course-123",
                timeback_id="student-456",
                payload={
                    "id": "activity-abc",
                    "endedAt": "2024-03-15",
                    "metrics": {"masteredUnits": 10},
                },
                course_config={"metadata": {"metrics": {"totalLessons": 100}}},
                env="staging",
            )

        # Conservative: only historical (20), assume already processed
        assert result == 20
        assert "Unexpected error fetching weekly facts" in caplog.text
        assert "assuming already processed" in caplog.text

    @pytest.mark.asyncio
    async def test_includes_current_when_payload_missing_id(self) -> None:
        """Should include current masteredUnits when payload has no activity ID."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Should NOT call get_weekly_facts when no activity ID
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                # No "id" field
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (20) + current (10) = 30%
        assert result == 30
        mock_client.edubridge.analytics.get_weekly_facts.assert_not_called()

    @pytest.mark.asyncio
    async def test_includes_current_when_payload_missing_ended_at(self) -> None:
        """Should include current masteredUnits when payload has no endedAt."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Should NOT call get_weekly_facts when no endedAt
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock()

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                # No "endedAt" field
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (20) + current (10) = 30%
        assert result == 30
        mock_client.edubridge.analytics.get_weekly_facts.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_empty_weekly_facts_list(self) -> None:
        """Should include current masteredUnits when weekly facts is empty."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(20)
        )
        # Empty weekly facts
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(return_value=[])

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Historical (20) + current (10) = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_handles_weekly_facts_as_dicts(self) -> None:
        """Should handle weekly facts returned as dict objects instead of model instances."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(30)
        )
        # Weekly facts as dict (some APIs return raw dicts)
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[
                {
                    "activityId": "activity-abc",
                    "enrollmentId": "enrollment-1",
                    "courseId": None,
                }
            ]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Only historical (30), current NOT added = 30%
        assert result == 30

    @pytest.mark.asyncio
    async def test_prevents_premature_100_percent_on_retry(self) -> None:
        """Regression test: retry should not inflate progress to 100% prematurely."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        # Historical already includes this activity (90 mastered from original + 10 current)
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value=create_mock_facts(100)  # Already at 100%
        )
        # Weekly facts confirms already processed
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(
            return_value=[create_mock_weekly_fact("activity-abc", "enrollment-1")]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        # Should stay at 100%, NOT become 110% (clamped anyway, but logic is correct)
        assert result == 100

    @pytest.mark.asyncio
    async def test_calls_weekly_facts_with_correct_parameters(self) -> None:
        """Should call get_weekly_facts with correct student_id and week_date."""
        mock_client = MagicMock()
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[create_mock_enrollment("enrollment-1", "course-123")]
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(return_value={})
        mock_client.edubridge.analytics.get_weekly_facts = AsyncMock(return_value=[])

        await compute_progress(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            payload={
                "id": "activity-abc",
                "endedAt": "2024-03-15T10:30:00Z",
                "metrics": {"masteredUnits": 10},
            },
            course_config={"metadata": {"metrics": {"totalLessons": 100}}},
            env="staging",
        )

        mock_client.edubridge.analytics.get_weekly_facts.assert_called_once_with(
            student_id="student-456",
            week_date="2024-03-15T10:30:00Z",
        )
