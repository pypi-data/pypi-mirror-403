"""Tests for canonical activity URL building."""

from typing import Any

import pytest

from timeback.server.handlers.activity import InvalidSensorUrlError
from timeback.server.handlers.activity.caliper import (
    build_activity_context,
    build_canonical_activity_url,
)
from timeback.shared.types import CourseCodeRef, SubjectGradeCourseRef


class TestBuildCanonicalActivityUrl:
    """Tests for build_canonical_activity_url."""

    def test_grade_based_course_url(self) -> None:
        """Should build URL for grade-based course: {sensor}/activities/{subject}/g{grade}/{slug}."""
        url = build_canonical_activity_url(
            sensor="https://sensor.example.com",
            selector=SubjectGradeCourseRef(subject="Math", grade=3),
            slug="fractions-with-like-denominators",
        )
        assert (
            url == "https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_grade_less_course_url(self) -> None:
        """Should build URL for grade-less course: {sensor}/activities/{code}/{slug}."""
        url = build_canonical_activity_url(
            sensor="https://sensor.example.com",
            selector=CourseCodeRef(code="CS-101"),
            slug="intro-to-loops",
        )
        assert url == "https://sensor.example.com/activities/CS-101/intro-to-loops"

    def test_encodes_special_characters_in_slug(self) -> None:
        """Should URI-encode special characters in slug."""
        url = build_canonical_activity_url(
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
        url = build_canonical_activity_url(
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
        url = build_canonical_activity_url(
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
            build_canonical_activity_url(
                sensor="not-a-valid-url",
                selector=SubjectGradeCourseRef(subject="Math", grade=3),
                slug="test",
            )
        assert exc_info.value.sensor == "not-a-valid-url"
        assert "Invalid sensor URL" in str(exc_info.value)

    def test_relative_url_raises(self) -> None:
        """Should raise InvalidSensorUrlError for relative URL."""
        with pytest.raises(InvalidSensorUrlError) as exc_info:
            build_canonical_activity_url(
                sensor="/api/caliper",
                selector=SubjectGradeCourseRef(subject="Math", grade=3),
                slug="test",
            )
        assert exc_info.value.sensor == "/api/caliper"


class TestBuildActivityContext:
    """Tests for build_activity_context with canonical URLs."""

    _OR_BASE_URL = "https://api.example.com"
    _OR_ROSTERING_PATH = "/ims/oneroster/rostering/v1p2"

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

    def _build_context(
        self,
        *,
        activity_id: str = "fractions-with-like-denominators",
        activity_name: str = "Fractions with Like Denominators",
        course_selector: Any = None,
        course_config: dict[str, Any] | None = None,
        app_name: str = "Test App",
        api_env: str = "staging",
        sensor: str = "https://sensor.example.com",
    ) -> Any:
        """Helper to build activity context with defaults."""
        return build_activity_context(
            activity_id=activity_id,
            activity_name=activity_name,
            course_selector=course_selector or SubjectGradeCourseRef(subject="Math", grade=3),
            course_config=course_config or self._grade_based_course(),
            app_name=app_name,
            api_env=api_env,
            sensor=sensor,
            oneroster_base_url=self._OR_BASE_URL,
            oneroster_rostering_path=self._OR_ROSTERING_PATH,
        )

    def test_context_id_is_canonical_url_grade_based(self) -> None:
        """Should set id to canonical URL for grade-based course."""
        context = self._build_context()
        assert (
            context.id
            == "https://sensor.example.com/activities/Math/g3/fractions-with-like-denominators"
        )

    def test_context_id_is_canonical_url_grade_less(self) -> None:
        """Should set id to canonical URL for grade-less course."""
        context = self._build_context(
            course_selector=CourseCodeRef(code="CS-101"),
            course_config=self._grade_less_course(),
        )
        assert (
            context.id
            == "https://sensor.example.com/activities/CS-101/fractions-with-like-denominators"
        )

    def test_activity_contains_only_name(self) -> None:
        """Activity field should contain only name, not id."""
        context = self._build_context()
        assert context.activity.name == "Fractions with Like Denominators"
        assert context.activity.id is None

    def test_type_is_set(self) -> None:
        """Should set correct type."""
        context = self._build_context()
        assert context.type == "TimebackActivityContext"

    def test_subject_from_course(self) -> None:
        """Should set subject from course."""
        context = self._build_context()
        assert context.subject == "Math"

    def test_app_name(self) -> None:
        """Should set app name."""
        context = self._build_context()
        assert context.app.name == "Test App"

    def test_course_id_and_name_staging(self) -> None:
        """Should set course id and name for staging."""
        context = self._build_context()
        assert (
            context.course.id
            == "https://api.example.com/ims/oneroster/rostering/v1p2/courses/course-math-3-staging"
        )
        assert context.course.name == "MATH-3"

    def test_course_id_and_name_production(self) -> None:
        """Should set course id and name for production."""
        context = self._build_context(api_env="production")
        assert (
            context.course.id
            == "https://api.example.com/ims/oneroster/rostering/v1p2/courses/course-math-3-prod"
        )
        assert context.course.name == "MATH-3"

    def test_invalid_sensor_raises(self) -> None:
        """Should raise InvalidSensorUrlError for invalid sensor."""
        with pytest.raises(InvalidSensorUrlError):
            self._build_context(sensor="not-a-valid-url")
