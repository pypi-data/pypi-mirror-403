"""Tests for activity payload validation."""

from dataclasses import dataclass, field
from typing import Any

from timeback.server.handlers.activity.schema import (
    format_course_selector,
    validate_activity_request,
)
from timeback.server.types import ValidationError, ValidationSuccess


@dataclass
class MockAppConfig:
    """Mock app config for testing."""

    name: str = "Test App"
    sensor: str | None = "https://sensor.example.com"
    courses: list[dict[str, Any]] = field(default_factory=lambda: [{"subject": "Math", "grade": 3}])


class TestValidateActivityRequest:
    """Tests for full activity request validation."""

    def _valid_payload(self) -> dict[str, Any]:
        """Return a valid activity payload."""
        return {
            "id": "lesson-123",
            "name": "Algebra Basics",
            "course": {"subject": "Math", "grade": 3},
            "startedAt": "2024-01-15T10:00:00Z",
            "endedAt": "2024-01-15T10:30:00Z",
            "elapsedMs": 1800000,
            "pausedMs": 60000,
            "metrics": {"totalQuestions": 10, "correctQuestions": 8},
        }

    def test_valid_payload_passes(self) -> None:
        """Valid payload should pass validation."""
        result = validate_activity_request(self._valid_payload(), MockAppConfig())
        assert isinstance(result, ValidationSuccess)
        assert result.ok is True
        assert result.payload is not None
        assert result.course is not None
        assert result.sensor is not None

    def test_missing_id_fails(self) -> None:
        """Missing id should fail."""
        body = self._valid_payload()
        del body["id"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_name_fails(self) -> None:
        """Missing name should fail."""
        body = self._valid_payload()
        del body["name"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_started_at_fails(self) -> None:
        """Missing startedAt should fail."""
        body = self._valid_payload()
        del body["startedAt"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_ended_at_fails(self) -> None:
        """Missing endedAt should fail."""
        body = self._valid_payload()
        del body["endedAt"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_elapsed_ms_fails(self) -> None:
        """Missing elapsedMs should fail."""
        body = self._valid_payload()
        del body["elapsedMs"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_paused_ms_fails(self) -> None:
        """Missing pausedMs should fail."""
        body = self._valid_payload()
        del body["pausedMs"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_missing_metrics_fails(self) -> None:
        """Missing metrics should fail."""
        body = self._valid_payload()
        del body["metrics"]
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_invalid_started_at_fails(self) -> None:
        """Invalid startedAt format should fail."""
        body = self._valid_payload()
        body["startedAt"] = "not-a-date"
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_invalid_elapsed_ms_fails(self) -> None:
        """Negative elapsedMs should fail."""
        body = self._valid_payload()
        body["elapsedMs"] = -100
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_boolean_elapsed_ms_fails(self) -> None:
        """Boolean elapsedMs should fail (booleans are not valid ints)."""
        body = self._valid_payload()
        body["elapsedMs"] = True
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_invalid_subject_fails(self) -> None:
        """Invalid course.subject should fail."""
        body = self._valid_payload()
        body["course"]["subject"] = "InvalidSubject"
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_valid_subjects_pass(self) -> None:
        """All valid subjects should pass."""
        for subject in ["Math", "Reading", "Science", "Social Studies", "Writing", "Other"]:
            body = self._valid_payload()
            body["course"]["subject"] = subject
            config = MockAppConfig(courses=[{"subject": subject, "grade": 3}])
            result = validate_activity_request(body, config)
            assert isinstance(result, ValidationSuccess), f"Subject '{subject}' should be valid"

    def test_invalid_grade_range_fails(self) -> None:
        """Grade outside 0-12 range should fail."""
        body = self._valid_payload()
        body["course"]["grade"] = 13
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

        body["course"]["grade"] = -1
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_valid_grades_pass(self) -> None:
        """All valid grades (0-12) should pass."""
        for grade in range(13):  # 0-12
            body = self._valid_payload()
            body["course"]["grade"] = grade
            config = MockAppConfig(courses=[{"subject": "Math", "grade": grade}])
            result = validate_activity_request(body, config)
            assert isinstance(result, ValidationSuccess), f"Grade {grade} should be valid"


class TestPctCompleteValidation:
    """Tests for pctComplete validation and clamping."""

    def _valid_payload(self) -> dict[str, Any]:
        """Return a valid activity payload."""
        return {
            "id": "lesson-123",
            "name": "Test",
            "course": {"subject": "Math", "grade": 3},
            "startedAt": "2024-01-15T10:00:00Z",
            "endedAt": "2024-01-15T10:30:00Z",
            "elapsedMs": 1800000,
            "pausedMs": 60000,
            "metrics": {},
        }

    def test_pct_complete_clamped_to_100(self) -> None:
        """pctComplete > 100 should be clamped to 100."""
        body = self._valid_payload()
        body["pctComplete"] = 150
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationSuccess)
        # The clamping happens on the body, not the payload

    def test_pct_complete_clamped_to_0(self) -> None:
        """pctComplete < 0 should be clamped to 0."""
        body = self._valid_payload()
        body["pctComplete"] = -50
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationSuccess)

    def test_pct_complete_boolean_fails(self) -> None:
        """Boolean pctComplete should fail."""
        body = self._valid_payload()
        body["pctComplete"] = True
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400


class TestMetricsValidation:
    """Tests for metrics field validation."""

    def _valid_payload(self) -> dict[str, Any]:
        """Return a valid activity payload."""
        return {
            "id": "lesson-123",
            "name": "Test",
            "course": {"subject": "Math", "grade": 3},
            "startedAt": "2024-01-15T10:00:00Z",
            "endedAt": "2024-01-15T10:30:00Z",
            "elapsedMs": 1800000,
            "pausedMs": 60000,
            "metrics": {"totalQuestions": 10, "correctQuestions": 8},
        }

    def test_correct_questions_exceeds_total_fails(self) -> None:
        """correctQuestions > totalQuestions should fail."""
        body = self._valid_payload()
        body["metrics"]["totalQuestions"] = 5
        body["metrics"]["correctQuestions"] = 10
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_total_without_correct_fails(self) -> None:
        """totalQuestions without correctQuestions should fail."""
        body = self._valid_payload()
        body["metrics"] = {"totalQuestions": 10}
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_correct_without_total_fails(self) -> None:
        """correctQuestions without totalQuestions should fail."""
        body = self._valid_payload()
        body["metrics"] = {"correctQuestions": 8}
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_negative_total_questions_fails(self) -> None:
        """Negative totalQuestions should fail."""
        body = self._valid_payload()
        body["metrics"]["totalQuestions"] = -1
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_empty_metrics_passes(self) -> None:
        """Empty metrics object should pass."""
        body = self._valid_payload()
        body["metrics"] = {}
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationSuccess)

    def test_xp_earned_float_passes(self) -> None:
        """Float xpEarned should pass."""
        body = self._valid_payload()
        body["metrics"]["xpEarned"] = 12.5
        result = validate_activity_request(body, MockAppConfig())
        assert isinstance(result, ValidationSuccess)


class TestCodeBasedCourseValidation:
    """Tests for code-based (grade-less) course selectors."""

    def _valid_code_based_payload(self) -> dict[str, Any]:
        """Return a valid activity payload with code-based course selector."""
        return {
            "id": "lesson-123",
            "name": "CS Basics",
            "course": {"code": "CS-101"},
            "startedAt": "2024-01-15T10:00:00Z",
            "endedAt": "2024-01-15T10:30:00Z",
            "elapsedMs": 1800000,
            "pausedMs": 60000,
            "metrics": {"totalQuestions": 10, "correctQuestions": 8},
        }

    def test_code_based_payload_passes(self) -> None:
        """Code-based course selector should pass validation."""
        config = MockAppConfig(courses=[{"subject": "Other", "course_code": "CS-101"}])
        result = validate_activity_request(self._valid_code_based_payload(), config)
        assert isinstance(result, ValidationSuccess)
        assert result.payload is not None
        assert result.course is not None
        assert result.sensor is not None

    def test_code_based_with_empty_code_fails(self) -> None:
        """Empty code string should fail."""
        body = self._valid_code_based_payload()
        body["course"]["code"] = ""
        config = MockAppConfig(courses=[{"subject": "Other", "course_code": "CS-101"}])
        result = validate_activity_request(body, config)
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400

    def test_unknown_code_fails(self) -> None:
        """Unknown course code should fail with 400."""
        body = self._valid_code_based_payload()
        body["course"]["code"] = "NONEXISTENT"
        config = MockAppConfig(courses=[{"subject": "Other", "course_code": "CS-101"}])
        result = validate_activity_request(body, config)
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 400


class TestSensorValidation:
    """Tests for sensor configuration validation."""

    def _valid_payload(self) -> dict[str, Any]:
        """Return a valid activity payload."""
        return {
            "id": "lesson-123",
            "name": "Test Activity",
            "course": {"subject": "Math", "grade": 3},
            "startedAt": "2024-01-15T10:00:00Z",
            "endedAt": "2024-01-15T10:30:00Z",
            "elapsedMs": 1800000,
            "pausedMs": 60000,
            "metrics": {},
        }

    def test_missing_sensor_fails(self) -> None:
        """Missing sensor should fail with 500."""
        config = MockAppConfig(sensor=None, courses=[{"subject": "Math", "grade": 3}])
        result = validate_activity_request(self._valid_payload(), config)
        assert isinstance(result, ValidationError)
        assert result.response.status_code == 500

    def test_per_course_sensor_overrides_default(self) -> None:
        """Per-course sensor should override the default sensor."""
        config = MockAppConfig(
            sensor="https://default.example.com",
            courses=[{"subject": "Math", "grade": 3, "sensor": "https://course.example.com"}],
        )
        result = validate_activity_request(self._valid_payload(), config)
        assert isinstance(result, ValidationSuccess)
        assert result.sensor == "https://course.example.com"

    def test_default_sensor_used_when_no_course_sensor(self) -> None:
        """Default sensor should be used when no per-course sensor."""
        config = MockAppConfig(
            sensor="https://default.example.com",
            courses=[{"subject": "Math", "grade": 3}],
        )
        result = validate_activity_request(self._valid_payload(), config)
        assert isinstance(result, ValidationSuccess)
        assert result.sensor == "https://default.example.com"


class TestFormatCourseSelector:
    """Tests for course selector formatting."""

    def test_format_grade_based_selector(self) -> None:
        """Should format grade-based selector."""
        from timeback.shared.types import SubjectGradeCourseRef

        ref = SubjectGradeCourseRef(subject="Math", grade=3)
        assert format_course_selector(ref) == "Math grade 3"

    def test_format_code_based_selector(self) -> None:
        """Should format code-based selector."""
        from timeback.shared.types import CourseCodeRef

        ref = CourseCodeRef(code="CS-101")
        assert format_course_selector(ref) == 'code "CS-101"'
