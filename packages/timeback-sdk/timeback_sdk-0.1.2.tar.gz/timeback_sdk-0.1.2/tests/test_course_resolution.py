"""Tests for course environment resolution."""

from timeback.server.timeback import (
    CourseConfig,
    CourseMetadata,
    _merge_metadata,
    _resolve_course_for_env,
)


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
