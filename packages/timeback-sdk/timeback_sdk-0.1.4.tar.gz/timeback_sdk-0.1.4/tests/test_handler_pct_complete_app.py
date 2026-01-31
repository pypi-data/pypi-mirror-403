"""Tests for pctCompleteApp calculation and Caliper event building.

Tests verify:
1. build_activity_events correctly includes/excludes generated_extensions
2. compute_progress returns correct values or None based on enrollment state
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from timeback.server.handlers.activity import compute_progress
from timeback.server.handlers.activity.caliper import (
    build_activity_context,
    build_activity_events,
    build_activity_metrics,
    build_time_spent_metrics,
)
from timeback.shared.types import SubjectGradeCourseRef
from timeback_caliper import TimebackUser
from timeback_common import ServerError

# ─────────────────────────────────────────────────────────────────────────────
# Test: pctCompleteApp in generated extensions
# ─────────────────────────────────────────────────────────────────────────────


class TestPctCompleteAppInGeneratedEvents:
    """Tests that pctCompleteApp flows through to Caliper events."""

    _SENSOR = "https://sensor.example.com"
    _OR_BASE_URL = "https://api.example.com"
    _OR_ROSTERING_PATH = "/ims/oneroster/rostering/v1p2"

    def _create_actor(self) -> TimebackUser:
        """Create a test actor."""
        return TimebackUser(
            id=f"{self._OR_BASE_URL}{self._OR_ROSTERING_PATH}/users/student-123",
            type="TimebackUser",
            email="student@example.edu",
        )

    def _create_activity_context(self, course_config: dict[str, Any]) -> Any:
        """Create a test activity context."""
        return build_activity_context(
            activity_id="lesson-1",
            activity_name="Test Lesson",
            course_selector=SubjectGradeCourseRef(subject="Math", grade=3),
            course_config=course_config,
            app_name="Test App",
            api_env="staging",
            sensor=self._SENSOR,
            oneroster_base_url=self._OR_BASE_URL,
            oneroster_rostering_path=self._OR_ROSTERING_PATH,
        )

    def test_pct_complete_app_appears_in_activity_event_when_provided(self) -> None:
        """
        FAILING TEST: pctCompleteApp should appear in ActivityEvent.generated.extensions
        when generated_extensions is provided.

        This test proves that the Caliper event building correctly includes
        pctCompleteApp in the generated object's extensions.
        """
        course_config = {
            "subject": "Math",
            "grade": 3,
            "ids": {"staging": "course-123"},
            "metadata": {"metrics": {"totalLessons": 100}},
        }

        actor = self._create_actor()
        activity_context = self._create_activity_context(course_config)
        activity_metrics = build_activity_metrics(
            {"totalQuestions": 10, "correctQuestions": 10, "masteredUnits": 13}
        )
        time_spent_metrics = build_time_spent_metrics(elapsed_ms=5000, paused_ms=0)

        # This is what the handler should provide when compute_progress returns a value
        pct_complete = 50
        generated_extensions = {"pctCompleteApp": pct_complete}

        activity_event, _time_spent_event = build_activity_events(
            actor=actor,
            activity_context=activity_context,
            activity_metrics=activity_metrics,
            time_spent_metrics=time_spent_metrics,
            event_time="2024-03-15T10:00:00Z",
            attempt=1,
            generated_extensions=generated_extensions,
            event_extensions={"courseId": "course-123"},
        )

        # ASSERTION: pctCompleteApp should be in generated.extensions
        assert activity_event.generated is not None, "generated should not be None"
        assert activity_event.generated.extensions is not None, (
            "generated.extensions should not be None when pctCompleteApp is computed"
        )
        assert activity_event.generated.extensions.get("pctCompleteApp") == pct_complete, (
            f"Expected pctCompleteApp={pct_complete} in generated.extensions, "
            f"got: {activity_event.generated.extensions}"
        )

    def test_pct_complete_app_is_none_when_not_provided(self) -> None:
        """
        When generated_extensions is None (compute_progress returned None),
        the generated.extensions should be None.
        """
        course_config = {
            "subject": "Math",
            "grade": 3,
            "ids": {"staging": "course-123"},
        }

        actor = self._create_actor()
        activity_context = self._create_activity_context(course_config)
        activity_metrics = build_activity_metrics({"totalQuestions": 10, "correctQuestions": 10})
        time_spent_metrics = build_time_spent_metrics(elapsed_ms=5000, paused_ms=0)

        # No generated_extensions (compute_progress returned None)
        activity_event, _ = build_activity_events(
            actor=actor,
            activity_context=activity_context,
            activity_metrics=activity_metrics,
            time_spent_metrics=time_spent_metrics,
            event_time="2024-03-15T10:00:00Z",
            attempt=1,
            generated_extensions=None,  # No pctComplete computed
            event_extensions={"courseId": "course-123"},
        )

        # generated.extensions should be None
        assert activity_event.generated.extensions is None


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_progress behavior
# ─────────────────────────────────────────────────────────────────────────────


def create_mock_enrollment(enrollment_id: str, course_id: str) -> Any:
    """Create a mock enrollment object."""
    enrollment = MagicMock()
    enrollment.id = enrollment_id
    enrollment.course = MagicMock()
    enrollment.course.id = course_id
    return enrollment


class TestComputeProgress:
    """Tests for compute_progress function behavior."""

    @pytest.mark.asyncio
    async def test_returns_none_when_enrollment_not_found(self) -> None:
        """compute_progress returns None when no enrollment matches the course_id."""
        mock_client = MagicMock()

        # Simulate: student has enrollments, but NONE match the course_id
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[
                create_mock_enrollment("enrollment-1", "different-course-id"),
                create_mock_enrollment("enrollment-2", "another-course-id"),
            ]
        )

        result = await compute_progress(
            client=mock_client,
            course_id="ba2dd859-7a40-49c3-80d5-2acfd80b3f2d",  # Production course ID
            timeback_id="a07975d5-dc67-4adf-bd13-b8e9203cbd29",  # Production user ID
            payload={"metrics": {"masteredUnits": 13}},  # Production payload
            course_config={
                "subject": "Other",
                "course_code": "BUNLEDGE",
                "metadata": {"metrics": {"totalLessons": 15}},  # Production config
            },
            env="production",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_value_when_enrollment_exists(self) -> None:
        """compute_progress returns calculated pctComplete when enrollment is found."""
        from timeback_edubridge.types.analytics import (
            ActivityMetricsData,
            SubjectMetrics,
            TimeSpentMetricsData,
        )

        mock_client = MagicMock()

        # Simulate: student HAS an enrollment matching the course_id
        mock_client.edubridge.enrollments.list = AsyncMock(
            return_value=[
                create_mock_enrollment("enrollment-123", "ba2dd859-7a40-49c3-80d5-2acfd80b3f2d"),
            ]
        )

        # Mock facts with some historical mastered units
        subject_metrics = SubjectMetrics(
            activity_metrics=ActivityMetricsData(
                xp_earned=100.0,
                total_questions=20,
                correct_questions=15,
                mastered_units=2,  # Historical: 2 mastered units
            ),
            time_spent_metrics=TimeSpentMetricsData(
                active_seconds=300,
                inactive_seconds=60,
                waste_seconds=10,
            ),
            apps=["TestApp"],
        )
        mock_client.edubridge.analytics.get_enrollment_facts = AsyncMock(
            return_value={"2024-03-15": {"Other": subject_metrics}}
        )

        result = await compute_progress(
            client=mock_client,
            course_id="ba2dd859-7a40-49c3-80d5-2acfd80b3f2d",
            timeback_id="a07975d5-dc67-4adf-bd13-b8e9203cbd29",
            payload={"metrics": {"masteredUnits": 13}},  # Current: 13 mastered units
            course_config={
                "subject": "Other",
                "course_code": "BUNLEDGE",
                "metadata": {"metrics": {"totalLessons": 15}},
            },
            env="production",
        )

        # Historical (2) + current (13) = 15, 15/15 = 100%
        assert result == 100

    @pytest.mark.asyncio
    async def test_returns_none_when_api_fails(self) -> None:
        """compute_progress returns None (graceful failure) when EduBridge API fails."""
        mock_client = MagicMock()

        # Simulate: EduBridge API fails (e.g., 503 Service Unavailable)
        mock_client.edubridge.enrollments.list = AsyncMock(
            side_effect=ServerError("Service Unavailable", status_code=503)
        )

        result = await compute_progress(
            client=mock_client,
            course_id="ba2dd859-7a40-49c3-80d5-2acfd80b3f2d",
            timeback_id="a07975d5-dc67-4adf-bd13-b8e9203cbd29",
            payload={"metrics": {"masteredUnits": 13}},
            course_config={
                "subject": "Other",
                "course_code": "BUNLEDGE",
                "metadata": {"metrics": {"totalLessons": 15}},
            },
            env="production",
        )

        assert result is None
