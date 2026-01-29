"""Tests for canonical activity URL building."""

from typing import Any

import pytest

from timeback.server.handlers.activity import (
    InvalidSensorUrlError,
    _build_activity_context,
    _build_canonical_activity_url,
)
from timeback.shared.types import CourseCodeRef, SubjectGradeCourseRef


class TestBuildCanonicalActivityUrl:
    """Tests for _build_canonical_activity_url."""

    def test_grade_based_course_url(self) -> None:
        """Should build URL for grade-based course: {sensor}/activities/{subject}/g{grade}/{slug}."""
        url = _build_canonical_activity_url(
            sensor="https://sensor.example.com",
            selector=SubjectGradeCourseRef(subject="Math", grade=3),
            slug="fractions-with-like-denominators",
        )
        assert (
            url == "https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_grade_less_course_url(self) -> None:
        """Should build URL for grade-less course: {sensor}/activities/{code}/{slug}."""
        url = _build_canonical_activity_url(
            sensor="https://sensor.example.com",
            selector=CourseCodeRef(code="CS-101"),
            slug="intro-to-loops",
        )
        assert url == "https://sensor.example.com/activities/CS-101/intro-to-loops"

    def test_encodes_special_characters_in_slug(self) -> None:
        """Should URI-encode special characters in slug."""
        url = _build_canonical_activity_url(
            sensor="https://sensor.example.com",
            selector=SubjectGradeCourseRef(subject="Math", grade=3),
            slug="lesson #1: intro & overview",
        )
        assert (
            url
            == "https://sensor.example.com/activities/Math/g3/lesson%20%231%3A%20intro%20%26%20overview"
        )

    def test_sensor_with_existing_path(self) -> None:
        """Should handle sensor URL with existing path."""
        url = _build_canonical_activity_url(
            sensor="https://sensor.example.com/v1/caliper",
            selector=SubjectGradeCourseRef(subject="Math", grade=3),
            slug="fractions-with-like-denominators",
        )
        assert (
            url
            == "https://sensor.example.com/v1/caliper/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_sensor_with_trailing_slash(self) -> None:
        """Should handle sensor URL with trailing slash."""
        url = _build_canonical_activity_url(
            sensor="https://sensor.example.com/",
            selector=SubjectGradeCourseRef(subject="Math", grade=3),
            slug="fractions-with-like-denominators",
        )
        assert (
            url == "https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_invalid_sensor_url_raises(self) -> None:
        """Should raise InvalidSensorUrlError for invalid sensor URL."""
        with pytest.raises(InvalidSensorUrlError) as exc_info:
            _build_canonical_activity_url(
                sensor="not-a-valid-url",
                selector=SubjectGradeCourseRef(subject="Math", grade=3),
                slug="test",
            )
        assert exc_info.value.sensor == "not-a-valid-url"
        assert "Invalid sensor URL" in str(exc_info.value)

    def test_relative_url_raises(self) -> None:
        """Should raise InvalidSensorUrlError for relative URL."""
        with pytest.raises(InvalidSensorUrlError) as exc_info:
            _build_canonical_activity_url(
                sensor="/api/caliper",
                selector=SubjectGradeCourseRef(subject="Math", grade=3),
                slug="test",
            )
        assert exc_info.value.sensor == "/api/caliper"


class TestBuildActivityContext:
    """Tests for _build_activity_context with canonical URLs."""

    def _make_payload(
        self,
        activity_id: str = "fractions-with-like-denominators",
        activity_name: str = "Fractions with Like Denominators",
        course: Any = None,
    ) -> Any:
        """Create a mock ValidatedActivityPayload."""
        from timeback.server.handlers.activity import ValidatedActivityPayload

        return ValidatedActivityPayload(
            id=activity_id,
            name=activity_name,
            course=course or SubjectGradeCourseRef(subject="Math", grade=3),
            started_at="2026-01-15T10:00:00.000Z",
            ended_at="2026-01-15T10:30:00.000Z",
            elapsed_ms=1800000,
            paused_ms=0,
            metrics={},
        )

    def _grade_based_course(self) -> dict[str, Any]:
        """Return a grade-based course config."""
        return {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "ids": {"staging": "course-math-3-staging", "production": "course-math-3-prod"},
        }

    def _grade_less_course(self) -> dict[str, Any]:
        """Return a grade-less course config."""
        return {
            "subject": "Other",
            "course_code": "CS-101",
            "ids": {"staging": "course-cs-101-staging", "production": "course-cs-101-prod"},
        }

    def test_context_id_is_canonical_url_grade_based(self) -> None:
        """Should set id to canonical URL for grade-based course."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert (
            context.id
            == "https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_context_id_is_canonical_url_grade_less(self) -> None:
        """Should set id to canonical URL for grade-less course."""
        payload = self._make_payload(course=CourseCodeRef(code="CS-101"))
        context = _build_activity_context(
            payload,
            self._grade_less_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert (
            context.id
            == "https://sensor.example.com/activities/CS-101/fractions-with-like-denominators"
        )

    def test_activity_contains_only_name(self) -> None:
        """Activity field should contain only name, not id."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert context.activity.name == "Fractions with Like Denominators"
        assert context.activity.id is None

    def test_type_is_set(self) -> None:
        """Should set correct type."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert context.type == "TimebackActivityContext"

    def test_subject_from_course(self) -> None:
        """Should set subject from course."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert context.subject == "Math"

    def test_app_name(self) -> None:
        """Should set app name."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert context.app.name == "Test App"

    def test_course_id_and_name_staging(self) -> None:
        """Should set course id and name for staging."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "staging",
            "https://sensor.example.com",
        )
        assert context.course.id == "course-math-3-staging"
        assert context.course.name == "MATH-3"

    def test_course_id_and_name_production(self) -> None:
        """Should set course id and name for production."""
        context = _build_activity_context(
            self._make_payload(),
            self._grade_based_course(),
            "Test App",
            "production",
            "https://sensor.example.com",
        )
        assert context.course.id == "course-math-3-prod"
        assert context.course.name == "MATH-3"

    def test_invalid_sensor_raises(self) -> None:
        """Should raise InvalidSensorUrlError for invalid sensor."""
        with pytest.raises(InvalidSensorUrlError):
            _build_activity_context(
                self._make_payload(),
                self._grade_based_course(),
                "Test App",
                "staging",
                "not-a-valid-url",
            )
