"""
Activity Course Resolution

Resolves course selectors from activity payloads to configured courses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ....shared.types import ActivityCourseRef


# ─────────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────────


class ActivityCourseResolutionError(Exception):
    """Error thrown when a course selector cannot be resolved against config.

    Supports both grade-based and code-based selectors:
    - Grade-based: subject and grade are set, course_code is None
    - Code-based: course_code is set, subject and grade are None
    """

    def __init__(
        self,
        code: str,
        course_ref: ActivityCourseRef,
        count: int | None = None,
    ) -> None:
        from ....shared.types import CourseCodeRef, SubjectGradeCourseRef

        super().__init__(code)
        self.code = code
        self.count = count

        # Store selector info based on type
        if isinstance(course_ref, SubjectGradeCourseRef):
            self.subject = course_ref.subject
            self.grade = course_ref.grade
            self.course_code = None
        elif isinstance(course_ref, CourseCodeRef):
            self.subject = None
            self.grade = None
            self.course_code = course_ref.code
        else:
            self.subject = None
            self.grade = None
            self.course_code = None

    def format_selector(self) -> str:
        """Format the selector for error messages."""
        if self.course_code:
            return f'code "{self.course_code}"'
        return f"{self.subject} grade {self.grade}"

    @property
    def selector_description(self) -> str:
        """Get a human-readable description of the selector."""
        return self.format_selector()


# ─────────────────────────────────────────────────────────────────────────────
# Resolution
# ─────────────────────────────────────────────────────────────────────────────


def resolve_activity_course(
    courses: list[dict[str, Any]],
    course_ref: ActivityCourseRef,
) -> dict[str, Any]:
    """
    Resolve a course config entry from an activity course selector.

    Use case: Activity handler — match the client's course selector
    to a configured course in timeback.config.json.

    Supports two selector modes:
    - **Grade-based**: SubjectGradeCourseRef(subject, grade) — matches (subject, grade)
    - **Code-based**: CourseCodeRef(code) — matches courseCode
    """
    from ....shared.types import CourseCodeRef, SubjectGradeCourseRef

    if isinstance(course_ref, SubjectGradeCourseRef):
        # Grade-based: match by subject + grade
        matches = [
            c
            for c in courses
            if c.get("subject") == course_ref.subject and c.get("grade") == course_ref.grade
        ]
    elif isinstance(course_ref, CourseCodeRef):
        # Code-based: match by course_code (normalized from JSON courseCode)
        matches = [c for c in courses if c.get("course_code") == course_ref.code]

    if len(matches) == 0:
        raise ActivityCourseResolutionError("unknown_course", course_ref)

    if len(matches) > 1:
        raise ActivityCourseResolutionError("ambiguous_course", course_ref, len(matches))

    return matches[0]
