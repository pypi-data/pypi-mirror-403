"""Tests for course environment resolution."""

from typing import Any

from timeback.server.handlers.activity import resolve_activity_course
from timeback.server.timeback import (
    CourseConfig,
    CourseMetadata,
    _merge_metadata,
    _resolve_course_for_env,
)
from timeback.shared.types import CourseCodeRef


def _parse_raw_course(raw_course: dict[str, Any]) -> CourseConfig:
    """
    Parse a raw JSON-style course config into internal representation.

    This mirrors the parsing logic in timeback.py _load_config_from_file().
    Key normalization: courseCode (JSON camelCase) -> course_code (Python snake_case)
    """
    course: CourseConfig = {
        "subject": raw_course.get("subject", "Other"),
    }
    if "grade" in raw_course and raw_course.get("grade") is not None:
        course["grade"] = raw_course.get("grade")
    # JSON uses camelCase, internal uses snake_case
    if "courseCode" in raw_course:
        course["course_code"] = raw_course.get("courseCode")
    if "ids" in raw_course:
        course["ids"] = raw_course["ids"]
    return course


class TestJsonKeyNormalization:
    """
    Tests that verify JSON camelCase keys are normalized to Python snake_case.

    This is critical because:
    - timeback.config.json uses camelCase (e.g., "courseCode")
    - Internal Python code uses snake_case (e.g., "course_code")
    - Any mismatch will silently fail course resolution
    """

    def test_course_code_normalized_from_json(self) -> None:
        """courseCode in JSON should be accessible as course_code internally."""
        raw_json_course = {
            "subject": "Other",
            "courseCode": "BUNLEDGE",  # JSON camelCase
            "ids": {"staging": "abc-123"},
        }

        parsed = _parse_raw_course(raw_json_course)

        # Internal representation uses snake_case
        assert parsed.get("course_code") == "BUNLEDGE"
        # camelCase key should NOT exist internally
        assert "courseCode" not in parsed

    def test_resolve_uses_internal_key(self) -> None:
        """resolve_activity_course must use internal snake_case key."""
        # Simulate courses already parsed (as they'd be in AppConfig.courses)
        courses = [
            {"subject": "Other", "course_code": "BUNLEDGE", "ids": {"staging": "abc-123"}},
        ]

        # This should find the course
        result = resolve_activity_course(courses, CourseCodeRef(code="BUNLEDGE"))
        assert result["course_code"] == "BUNLEDGE"

    def test_end_to_end_json_to_resolution(self) -> None:
        """Full flow: JSON config -> parsing -> course resolution."""
        # Raw JSON as it would appear in timeback.config.json
        raw_json_courses = [
            {"subject": "Other", "courseCode": "BUNLEDGE", "ids": {"staging": "abc-123"}},
            {"subject": "Math", "grade": 3, "courseCode": "MATH-3", "ids": {"staging": "def-456"}},
        ]

        # Parse (simulating _load_config_from_file)
        parsed_courses = [_parse_raw_course(c) for c in raw_json_courses]

        # Resolve by code
        result = resolve_activity_course(parsed_courses, CourseCodeRef(code="BUNLEDGE"))
        assert result["course_code"] == "BUNLEDGE"

        result = resolve_activity_course(parsed_courses, CourseCodeRef(code="MATH-3"))
        assert result["course_code"] == "MATH-3"


class TestMergeMetadata:
    """Tests for metadata merging."""

    def test_both_none_returns_none(self) -> None:
        """Should return None when both inputs are None."""
        assert _merge_metadata(None, None) is None

    def test_base_none_returns_override(self) -> None:
        """Should return override when base is None."""
        override: CourseMetadata = {"goals": {"daily_xp": 100}}
        assert _merge_metadata(None, override) == override

    def test_override_none_returns_base(self) -> None:
        """Should return base when override is None."""
        base: CourseMetadata = {"goals": {"daily_xp": 100}}
        assert _merge_metadata(base, None) == base

    def test_deep_merges_goals(self) -> None:
        """Should deep merge goals, preserving unchanged values."""
        base: CourseMetadata = {
            "goals": {"daily_xp": 100, "daily_lessons": 5},
        }
        override: CourseMetadata = {
            "goals": {"daily_xp": 200},  # Override only daily_xp
        }
        result = _merge_metadata(base, override)
        assert result is not None
        assert result["goals"]["daily_xp"] == 200  # Overridden
        assert result["goals"]["daily_lessons"] == 5  # Preserved


class TestResolveCourseForEnv:
    """Tests for course environment resolution."""

    def test_returns_base_when_no_overrides(self) -> None:
        """Should return base course when no overrides exist."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "level": "Elementary",
            "sensor": "https://base.sensor.com",
        }

        resolved = _resolve_course_for_env(course, "staging")

        assert resolved["level"] == "Elementary"
        assert resolved["sensor"] == "https://base.sensor.com"

    def test_applies_staging_overrides(self) -> None:
        """Should apply staging-specific overrides."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "level": "Elementary",
            "sensor": "https://base.sensor.com",
            "overrides": {
                "staging": {
                    "level": "Staging Level",
                    "sensor": "https://staging.sensor.com",
                },
            },
        }

        resolved = _resolve_course_for_env(course, "staging")

        assert resolved["level"] == "Staging Level"
        assert resolved["sensor"] == "https://staging.sensor.com"

    def test_applies_production_overrides(self) -> None:
        """Should apply production-specific overrides."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "level": "Elementary",
            "sensor": "https://base.sensor.com",
            "overrides": {
                "production": {
                    "level": "Production Level",
                    "sensor": "https://prod.sensor.com",
                },
            },
        }

        resolved = _resolve_course_for_env(course, "production")

        assert resolved["level"] == "Production Level"
        assert resolved["sensor"] == "https://prod.sensor.com"

    def test_returns_base_when_env_has_no_overrides(self) -> None:
        """Should return base course when requested env has no overrides."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "level": "Elementary",
            "overrides": {
                "staging": {
                    "level": "Staging Only",
                },
            },
        }

        # Request production, but only staging override exists
        resolved = _resolve_course_for_env(course, "production")

        assert resolved["level"] == "Elementary"  # Base level, not staging override

    def test_partial_override_preserves_base(self) -> None:
        """Should preserve base values not in override."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "level": "Elementary",
            "sensor": "https://base.sensor.com",
            "overrides": {
                "staging": {
                    "level": "Staging Level",
                    # No sensor override
                },
            },
        }

        resolved = _resolve_course_for_env(course, "staging")

        assert resolved["level"] == "Staging Level"  # Overridden
        assert resolved["sensor"] == "https://base.sensor.com"  # Preserved

    def test_deep_merges_metadata(self) -> None:
        """Should deep merge metadata.goals."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "metadata": {
                "goals": {
                    "daily_xp": 100,
                    "daily_lessons": 5,
                },
            },
            "overrides": {
                "staging": {
                    "metadata": {
                        "goals": {
                            "daily_accuracy": 80,  # New goal
                        },
                    },
                },
            },
        }

        resolved = _resolve_course_for_env(course, "staging")

        assert resolved["metadata"] is not None
        assert resolved["metadata"]["goals"]["daily_xp"] == 100  # Preserved
        assert resolved["metadata"]["goals"]["daily_lessons"] == 5  # Preserved
        assert resolved["metadata"]["goals"]["daily_accuracy"] == 80  # Added

    def test_preserves_identity_fields(self) -> None:
        """Should preserve identity fields (subject, grade, course_code, ids)."""
        course: CourseConfig = {
            "subject": "Math",
            "grade": 3,
            "course_code": "MATH-3",
            "ids": {"staging": "staging-id", "production": "prod-id"},
            "overrides": {
                "staging": {
                    "level": "Staging Level",
                },
            },
        }

        resolved = _resolve_course_for_env(course, "staging")

        assert resolved["subject"] == "Math"
        assert resolved["grade"] == 3
        assert resolved["course_code"] == "MATH-3"
        assert resolved["ids"] == {"staging": "staging-id", "production": "prod-id"}
