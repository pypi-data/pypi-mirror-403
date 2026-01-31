"""Tests for the resolve module."""

import pytest

from timeback.server.handlers.activity.resolve import (
    ActivityCourseResolutionError,
    resolve_activity_course,
)
from timeback.server.lib.resolve import (
    TimebackUserResolutionError,
    resolve_status_for_user_resolution_error,
)
from timeback.shared.types import CourseCodeRef, SubjectGradeCourseRef


class TestResolveStatusForUserResolutionError:
    """Tests for resolve_status_for_user_resolution_error."""

    def test_ambiguous_returns_409(self) -> None:
        """Ambiguous user should return 409."""
        err = TimebackUserResolutionError("test", "timeback_user_ambiguous")
        assert resolve_status_for_user_resolution_error(err) == 409

    def test_not_found_returns_404(self) -> None:
        """Not found user should return 404."""
        err = TimebackUserResolutionError("test", "timeback_user_not_found")
        assert resolve_status_for_user_resolution_error(err) == 404

    def test_lookup_failed_returns_404(self) -> None:
        """Lookup failed should return 404."""
        err = TimebackUserResolutionError("test", "timeback_user_lookup_failed")
        assert resolve_status_for_user_resolution_error(err) == 404

    def test_missing_email_returns_404(self) -> None:
        """Missing email should return 404."""
        err = TimebackUserResolutionError("test", "missing_email")
        assert resolve_status_for_user_resolution_error(err) == 404


class TestResolveActivityCourseGradeBased:
    """Tests for resolve_activity_course with grade-based selectors."""

    def test_resolves_matching_course(self) -> None:
        """Should resolve a course that matches subject and grade."""
        courses = [
            {"subject": "Math", "grade": 5, "course_code": "MATH5"},
            {"subject": "Reading", "grade": 3, "course_code": "READ3"},
        ]
        course_ref = SubjectGradeCourseRef(subject="Math", grade=5)
        result = resolve_activity_course(courses, course_ref)
        assert result["course_code"] == "MATH5"

    def test_raises_unknown_course_error(self) -> None:
        """Should raise error when no course matches."""
        courses = [
            {"subject": "Math", "grade": 5, "course_code": "MATH5"},
        ]
        course_ref = SubjectGradeCourseRef(subject="Reading", grade=3)
        with pytest.raises(ActivityCourseResolutionError) as exc_info:
            resolve_activity_course(courses, course_ref)
        assert exc_info.value.code == "unknown_course"
        assert exc_info.value.subject == "Reading"
        assert exc_info.value.grade == 3

    def test_raises_ambiguous_course_error(self) -> None:
        """Should raise error when multiple courses match."""
        courses = [
            {"subject": "Math", "grade": 5, "course_code": "MATH5A"},
            {"subject": "Math", "grade": 5, "course_code": "MATH5B"},
        ]
        course_ref = SubjectGradeCourseRef(subject="Math", grade=5)
        with pytest.raises(ActivityCourseResolutionError) as exc_info:
            resolve_activity_course(courses, course_ref)
        assert exc_info.value.code == "ambiguous_course"
        assert exc_info.value.count == 2

    def test_empty_courses_raises_unknown(self) -> None:
        """Should raise unknown course error with empty courses list."""
        courses: list[dict] = []
        course_ref = SubjectGradeCourseRef(subject="Math", grade=5)
        with pytest.raises(ActivityCourseResolutionError) as exc_info:
            resolve_activity_course(courses, course_ref)
        assert exc_info.value.code == "unknown_course"


class TestResolveActivityCourseCodeBased:
    """Tests for resolve_activity_course with code-based selectors."""

    def test_resolves_matching_course_by_code(self) -> None:
        """Should resolve a course that matches by code."""
        courses = [
            {"subject": "Other", "course_code": "CS-101"},
            {"subject": "Other", "course_code": "CS-201"},
        ]
        course_ref = CourseCodeRef(code="CS-101")
        result = resolve_activity_course(courses, course_ref)
        assert result["course_code"] == "CS-101"

    def test_raises_unknown_course_error_for_code(self) -> None:
        """Should raise error when no course code matches."""
        courses = [
            {"subject": "Other", "course_code": "CS-101"},
        ]
        course_ref = CourseCodeRef(code="CS-999")
        with pytest.raises(ActivityCourseResolutionError) as exc_info:
            resolve_activity_course(courses, course_ref)
        assert exc_info.value.code == "unknown_course"
        assert exc_info.value.course_code == "CS-999"
        assert exc_info.value.subject is None

    def test_raises_ambiguous_course_error_for_code(self) -> None:
        """Should raise error when multiple course codes match (shouldn't happen with valid config)."""
        courses = [
            {"subject": "Other", "course_code": "CS-101"},
            {"subject": "Math", "course_code": "CS-101"},  # duplicate code
        ]
        course_ref = CourseCodeRef(code="CS-101")
        with pytest.raises(ActivityCourseResolutionError) as exc_info:
            resolve_activity_course(courses, course_ref)
        assert exc_info.value.code == "ambiguous_course"


class TestTimebackUserResolutionError:
    """Tests for TimebackUserResolutionError."""

    def test_error_has_code(self) -> None:
        """Error should have code attribute."""
        err = TimebackUserResolutionError("Test message", "timeback_user_not_found")
        assert err.code == "timeback_user_not_found"
        assert str(err) == "Test message"


class TestActivityCourseResolutionError:
    """Tests for ActivityCourseResolutionError."""

    def test_error_has_attributes_for_grade_based(self) -> None:
        """Error should have subject, grade, and count attributes for grade-based selector."""
        course_ref = SubjectGradeCourseRef(subject="Math", grade=5)
        err = ActivityCourseResolutionError("ambiguous_course", course_ref, 3)
        assert err.code == "ambiguous_course"
        assert err.subject == "Math"
        assert err.grade == 5
        assert err.course_code is None
        assert err.count == 3

    def test_error_has_attributes_for_code_based(self) -> None:
        """Error should have course_code attribute for code-based selector."""
        course_ref = CourseCodeRef(code="CS-101")
        err = ActivityCourseResolutionError("unknown_course", course_ref)
        assert err.code == "unknown_course"
        assert err.course_code == "CS-101"
        assert err.subject is None
        assert err.grade is None

    def test_format_selector_grade_based(self) -> None:
        """format_selector should work for grade-based errors."""
        course_ref = SubjectGradeCourseRef(subject="Math", grade=5)
        err = ActivityCourseResolutionError("unknown_course", course_ref)
        assert err.format_selector() == "Math grade 5"

    def test_format_selector_code_based(self) -> None:
        """format_selector should work for code-based errors."""
        course_ref = CourseCodeRef(code="CS-101")
        err = ActivityCourseResolutionError("unknown_course", course_ref)
        assert err.format_selector() == 'code "CS-101"'
