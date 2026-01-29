"""Tests for shared types."""

import pytest

from timeback.shared.types import (
    ActivityEndPayload,
    ActivityMetrics,
    CourseCodeRef,
    CourseInfo,
    GoalsInfo,
    IdentityClaims,
    SchoolInfo,
    SubjectGradeCourseRef,
    TimebackAuthUser,
    TimebackIdentity,
    TimebackProfile,
    XpInfo,
    is_subject_grade_course_ref,
)


class TestRootExports:
    """Tests for package root exports."""

    def test_exports_oidc_types(self) -> None:
        """Package root should export OIDC types."""
        from timeback import IdpData, OIDCTokens, OIDCUserInfo

        # Verify they are importable and are the expected types
        assert IdpData is not None
        assert OIDCTokens is not None
        assert OIDCUserInfo is not None

    def test_exports_resolution_error_code(self) -> None:
        """Package root should export TimebackUserResolutionErrorCode."""
        from timeback import TimebackUserResolutionErrorCode

        # Verify it's a Literal type alias with expected values
        assert TimebackUserResolutionErrorCode is not None


class TestTimebackIdentity:
    """Tests for TimebackIdentity."""

    def test_basic_identity(self) -> None:
        """Should create a basic identity."""
        identity = TimebackIdentity(id="user-123", email="test@example.com")
        assert identity.id == "user-123"
        assert identity.email == "test@example.com"
        assert identity.name is None

    def test_identity_with_name(self) -> None:
        """Should create an identity with name."""
        identity = TimebackIdentity(id="user-123", email="test@example.com", name="Test User")
        assert identity.name == "Test User"


class TestTimebackProfile:
    """Tests for TimebackProfile."""

    def test_minimal_profile(self) -> None:
        """Should create a minimal profile."""
        profile = TimebackProfile(id="user-123", email="test@example.com")
        assert profile.id == "user-123"
        assert profile.email == "test@example.com"
        assert profile.school is None
        assert profile.grade is None
        assert profile.xp is None
        assert profile.courses is None
        assert profile.goals is None

    def test_full_profile(self) -> None:
        """Should create a full profile with all fields."""
        profile = TimebackProfile(
            id="user-123",
            email="test@example.com",
            name="Test User",
            school=SchoolInfo(id="school-1", name="Test School"),
            grade=5,
            xp=XpInfo(today=100, all=1000),
            courses=[CourseInfo(id="course-1", code="MATH5", name="Math Grade 5")],
            goals=GoalsInfo(daily_xp=50, daily_lessons=3, daily_active_minutes=30),
        )
        assert profile.name == "Test User"
        assert profile.school.id == "school-1"
        assert profile.grade == 5
        assert profile.xp.today == 100
        assert profile.courses[0].code == "MATH5"
        assert profile.goals.daily_xp == 50


class TestTimebackAuthUser:
    """Tests for TimebackAuthUser."""

    def test_auth_user_with_claims(self) -> None:
        """Should create an auth user with claims."""
        auth_user = TimebackAuthUser(
            id="user-123",
            email="test@example.com",
            claims=IdentityClaims(
                sub="cognito-sub-123",
                email="test@example.com",
                first_name="Test",
                last_name="User",
            ),
        )
        assert auth_user.id == "user-123"
        assert auth_user.claims.sub == "cognito-sub-123"
        assert auth_user.claims.first_name == "Test"

    def test_claims_is_required(self) -> None:
        """TimebackAuthUser should require claims parameter."""
        # claims is a keyword-only required argument
        with pytest.raises(TypeError, match="claims"):
            TimebackAuthUser(  # type: ignore[call-arg]
                id="user-123",
                email="test@example.com",
            )


class TestActivityCourseRef:
    """Tests for ActivityCourseRef (union of SubjectGradeCourseRef | CourseCodeRef)."""

    def test_subject_grade_course_ref(self) -> None:
        """Should create a grade-based course reference."""
        ref = SubjectGradeCourseRef(subject="Math", grade=5)
        assert ref.subject == "Math"
        assert ref.grade == 5

    def test_course_code_ref(self) -> None:
        """Should create a code-based course reference."""
        ref = CourseCodeRef(code="CS-101")
        assert ref.code == "CS-101"

    def test_is_subject_grade_course_ref_true(self) -> None:
        """is_subject_grade_course_ref should return True for SubjectGradeCourseRef."""
        ref = SubjectGradeCourseRef(subject="Math", grade=5)
        assert is_subject_grade_course_ref(ref) is True

    def test_is_subject_grade_course_ref_false(self) -> None:
        """is_subject_grade_course_ref should return False for CourseCodeRef."""
        ref = CourseCodeRef(code="CS-101")
        assert is_subject_grade_course_ref(ref) is False


class TestActivityMetrics:
    """Tests for ActivityMetrics."""

    def test_empty_metrics(self) -> None:
        """Should create empty metrics."""
        metrics = ActivityMetrics()
        assert metrics.total_questions is None
        assert metrics.correct_questions is None
        assert metrics.xp_earned is None
        assert metrics.mastered_units is None

    def test_full_metrics(self) -> None:
        """Should create metrics with all fields."""
        metrics = ActivityMetrics(
            total_questions=10,
            correct_questions=8,
            xp_earned=50,
            mastered_units=2,
        )
        assert metrics.total_questions == 10
        assert metrics.correct_questions == 8


class TestActivityEndPayload:
    """Tests for ActivityEndPayload."""

    def test_activity_payload_with_grade_based_course(self) -> None:
        """Should create an activity payload with grade-based course."""
        payload = ActivityEndPayload(
            id="activity-1",
            name="Quiz 1",
            course=SubjectGradeCourseRef(subject="Math", grade=5),
            started_at="2024-01-15T10:00:00Z",
            ended_at="2024-01-15T10:30:00Z",
            elapsed_ms=1800000,
            paused_ms=0,
            metrics=ActivityMetrics(total_questions=10, correct_questions=8),
        )
        assert payload.id == "activity-1"
        assert is_subject_grade_course_ref(payload.course)
        assert payload.course.subject == "Math"
        assert payload.elapsed_ms == 1800000
        assert payload.metrics.total_questions == 10

    def test_activity_payload_with_code_based_course(self) -> None:
        """Should create an activity payload with code-based course."""
        payload = ActivityEndPayload(
            id="activity-2",
            name="CS Quiz",
            course=CourseCodeRef(code="CS-101"),
            started_at="2024-01-15T10:00:00Z",
            ended_at="2024-01-15T10:30:00Z",
            elapsed_ms=1800000,
            paused_ms=0,
            metrics=ActivityMetrics(),
        )
        assert payload.id == "activity-2"
        assert not is_subject_grade_course_ref(payload.course)
        assert payload.course.code == "CS-101"
