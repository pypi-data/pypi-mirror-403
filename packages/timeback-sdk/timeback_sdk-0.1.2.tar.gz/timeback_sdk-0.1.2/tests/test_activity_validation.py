"""Tests for activity payload validation."""

from dataclasses import dataclass, field
from typing import Any

from timeback.server.handlers.activity import (
    _is_nonnegative_int,
    _is_valid_iso_datetime,
    _validate_activity_request,
    _validation_error,
)


@dataclass
class MockAppConfig:
    """Mock app config for testing."""

    name: str = "Test App"
    sensor: str | None = "https://sensor.example.com"
    courses: list[dict[str, Any]] = field(default_factory=lambda: [{"subject": "Math", "grade": 3}])


class TestIsValidIsoDatetime:
    """Tests for ISO datetime validation."""

    def test_valid_datetime_with_z_suffix(self) -> None:
        """Should accept valid ISO datetime with Z suffix."""
        assert _is_valid_iso_datetime("2024-01-15T10:30:00Z") is True
        assert _is_valid_iso_datetime("2024-12-31T23:59:59Z") is True

    def test_valid_datetime_with_milliseconds(self) -> None:
        """Should accept valid ISO datetime with milliseconds."""
        assert _is_valid_iso_datetime("2024-01-15T10:30:00.123Z") is True
        assert _is_valid_iso_datetime("2024-01-15T10:30:00.999999Z") is True

    def test_valid_datetime_with_timezone_offset(self) -> None:
        """Should accept valid ISO datetime with timezone offset."""
        assert _is_valid_iso_datetime("2024-01-15T10:30:00+00:00") is True
        assert _is_valid_iso_datetime("2024-01-15T10:30:00-05:00") is True
        assert _is_valid_iso_datetime("2024-01-15T10:30:00+05:30") is True

    def test_invalid_datetime_formats(self) -> None:
        """Should reject invalid datetime formats."""
        assert _is_valid_iso_datetime("2024-01-15") is False  # Date only
        assert _is_valid_iso_datetime("10:30:00") is False  # Time only
        assert _is_valid_iso_datetime("2024/01/15T10:30:00Z") is False  # Wrong separator
        assert _is_valid_iso_datetime("not-a-date") is False
        assert _is_valid_iso_datetime("") is False

    def test_non_string_values(self) -> None:
        """Should reject non-string values."""
        assert _is_valid_iso_datetime(None) is False
        assert _is_valid_iso_datetime(123) is False
        assert _is_valid_iso_datetime(["2024-01-15T10:30:00Z"]) is False


class TestIsNonnegativeInt:
    """Tests for nonnegative integer validation."""

    def test_zero_is_valid(self) -> None:
        """Zero should be valid."""
        assert _is_nonnegative_int(0) is True

    def test_positive_integers_are_valid(self) -> None:
        """Positive integers should be valid."""
        assert _is_nonnegative_int(1) is True
        assert _is_nonnegative_int(100) is True
        assert _is_nonnegative_int(1000000) is True

    def test_negative_integers_are_invalid(self) -> None:
        """Negative integers should be invalid."""
        assert _is_nonnegative_int(-1) is False
        assert _is_nonnegative_int(-100) is False

    def test_floats_are_invalid(self) -> None:
        """Floats should be invalid (even if whole numbers)."""
        assert _is_nonnegative_int(0.0) is False
        assert _is_nonnegative_int(1.0) is False
        assert _is_nonnegative_int(1.5) is False

    def test_strings_are_invalid(self) -> None:
        """Strings should be invalid."""
        assert _is_nonnegative_int("0") is False
        assert _is_nonnegative_int("100") is False

    def test_booleans_are_invalid(self) -> None:
        """Booleans should be invalid (even though bool is subclass of int)."""
        assert _is_nonnegative_int(True) is False
        assert _is_nonnegative_int(False) is False

    def test_none_is_invalid(self) -> None:
        """None should be invalid."""
        assert _is_nonnegative_int(None) is False


class TestValidationError:
    """Tests for validation error response helper."""

    def test_creates_400_response(self) -> None:
        """Should create a 400 response with error details."""
        response = _validation_error("id", "Required")
        assert response.status_code == 400

    def test_response_body_structure(self) -> None:
        """Response body should have structured field/message details."""
        import json

        response = _validation_error("course.subject", "Invalid enum value")
        assert response.status_code == 400

        # Parse the response body
        body = json.loads(response.body.decode())
        assert body["success"] is False
        assert body["error"] == "Invalid payload"
        assert body["details"] == {"field": "course.subject", "message": "Invalid enum value"}


class TestValidateActivityRequest:
    """Tests for full activity request validation (matching TS SDK strictness)."""

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
        payload, course, sensor, error = _validate_activity_request(
            self._valid_payload(), MockAppConfig()
        )
        assert error is None
        assert payload is not None
        assert course is not None
        assert sensor is not None

    def test_missing_started_at_fails(self) -> None:
        """Missing startedAt should fail (matches TS SDK strictness)."""
        body = self._valid_payload()
        del body["startedAt"]
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_missing_ended_at_fails(self) -> None:
        """Missing endedAt should fail (matches TS SDK strictness)."""
        body = self._valid_payload()
        del body["endedAt"]
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_missing_elapsed_ms_fails(self) -> None:
        """Missing elapsedMs should fail (matches TS SDK strictness)."""
        body = self._valid_payload()
        del body["elapsedMs"]
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_missing_paused_ms_fails(self) -> None:
        """Missing pausedMs should fail (matches TS SDK strictness)."""
        body = self._valid_payload()
        del body["pausedMs"]
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_missing_metrics_fails(self) -> None:
        """Missing metrics should fail (matches TS SDK strictness)."""
        body = self._valid_payload()
        del body["metrics"]
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_invalid_subject_fails(self) -> None:
        """Invalid course.subject should fail (matches TS SDK enum validation)."""
        body = self._valid_payload()
        body["course"]["subject"] = "InvalidSubject"
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_valid_subjects_pass(self) -> None:
        """All valid subjects should pass."""
        for subject in ["Math", "Reading", "Science", "Social Studies", "Writing", "Other"]:
            body = self._valid_payload()
            body["course"]["subject"] = subject
            config = MockAppConfig(courses=[{"subject": subject, "grade": 3}])
            _, _, _, error = _validate_activity_request(body, config)
            assert error is None, f"Subject '{subject}' should be valid"

    def test_invalid_grade_range_fails(self) -> None:
        """Grade outside 0-12 range should fail (matches TS SDK enum validation)."""
        body = self._valid_payload()
        body["course"]["grade"] = 13
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

        body["course"]["grade"] = -1
        _, _, _, error = _validate_activity_request(body, MockAppConfig())
        assert error is not None
        assert error.status_code == 400

    def test_valid_grades_pass(self) -> None:
        """All valid grades (0-12) should pass."""
        for grade in range(13):  # 0-12
            body = self._valid_payload()
            body["course"]["grade"] = grade
            config = MockAppConfig(courses=[{"subject": "Math", "grade": grade}])
            _, _, _, error = _validate_activity_request(body, config)
            assert error is None, f"Grade {grade} should be valid"


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
        payload, course, sensor, error = _validate_activity_request(
            self._valid_code_based_payload(), config
        )
        assert error is None
        assert payload is not None
        assert course is not None
        assert sensor is not None

    def test_code_based_with_empty_code_fails(self) -> None:
        """Empty code string should fail."""
        body = self._valid_code_based_payload()
        body["course"]["code"] = ""
        config = MockAppConfig(courses=[{"subject": "Other", "course_code": "CS-101"}])
        _, _, _, error = _validate_activity_request(body, config)
        assert error is not None
        assert error.status_code == 400

    def test_unknown_code_fails(self) -> None:
        """Unknown course code should fail with 400."""
        body = self._valid_code_based_payload()
        body["course"]["code"] = "NONEXISTENT"
        config = MockAppConfig(courses=[{"subject": "Other", "course_code": "CS-101"}])
        _, _, _, error = _validate_activity_request(body, config)
        assert error is not None
        assert error.status_code == 400


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
        _, _, _, error = _validate_activity_request(self._valid_payload(), config)
        assert error is not None
        assert error.status_code == 500

    def test_per_course_sensor_overrides_default(self) -> None:
        """Per-course sensor should override the default sensor."""
        config = MockAppConfig(
            sensor="https://default.example.com",
            courses=[{"subject": "Math", "grade": 3, "sensor": "https://course.example.com"}],
        )
        _, _course, sensor, error = _validate_activity_request(self._valid_payload(), config)
        assert error is None
        assert sensor == "https://course.example.com"

    def test_default_sensor_used_when_no_course_sensor(self) -> None:
        """Default sensor should be used when no per-course sensor."""
        config = MockAppConfig(
            sensor="https://default.example.com",
            courses=[{"subject": "Math", "grade": 3}],
        )
        _, _course, sensor, error = _validate_activity_request(self._valid_payload(), config)
        assert error is None
        assert sensor == "https://default.example.com"
