"""Tests for activity gradebook (OneRoster) functionality."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from timeback.server.handlers.activity import (
    _build_activity_context,
    resolve_attempt_number,
    write_gradebook_entry,
)
from timeback.server.lib.utils import hash_suffix_64_base36
from timeback.shared.types import SubjectGradeCourseRef

# ─────────────────────────────────────────────────────────────────────────────
# Test: process=False in activity context
# ─────────────────────────────────────────────────────────────────────────────


class TestActivityContextProcessFlag:
    """Tests for process=False in activity context builder."""

    def test_activity_context_has_process_false(self) -> None:
        """Activity context should have process=False."""
        from timeback.server.handlers.activity.handler import ValidatedActivityPayload

        payload = ValidatedActivityPayload(
            id="lesson-123",
            name="Test Lesson",
            course=SubjectGradeCourseRef(subject="Math", grade=3),
            started_at="2024-01-15T10:00:00Z",
            ended_at="2024-01-15T10:30:00Z",
            elapsed_ms=1800000,
            paused_ms=0,
            metrics={},
        )

        course_config = {
            "subject": "Math",
            "grade": 3,
            "ids": {"staging": "course-123"},
        }

        context = _build_activity_context(
            payload,
            course_config,
            "Test App",
            "staging",
            "https://sensor.example.com",
        )

        assert context.process is False


# ─────────────────────────────────────────────────────────────────────────────
# Test: resolve_attempt_number
# ─────────────────────────────────────────────────────────────────────────────


def create_mock_result(attempt: int, ended_at: str) -> dict[str, Any]:
    """Create a mock assessment result for testing."""
    ended_at_hash = hash_suffix_64_base36(ended_at)
    return {
        "sourcedId": f"test-line-item:student-456:attempt-{attempt}:e-{ended_at_hash}",
        "status": "active",
        "assessmentLineItem": {"sourcedId": "test-line-item"},
        "student": {"sourcedId": "student-456"},
        "score": 80,
        "scoreDate": ended_at,
        "scoreStatus": "fully graded",
        "metadata": {
            "attempt": attempt,
            "endedAt": ended_at,
        },
    }


class TestResolveAttemptNumber:
    """Tests for resolve_attempt_number function."""

    @pytest.mark.asyncio
    async def test_returns_1_when_no_existing_results(self) -> None:
        """Should return 1 when there are no existing results."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])

        attempt = await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",
        )

        assert attempt == 1

    @pytest.mark.asyncio
    async def test_returns_max_plus_1_for_new_attempt(self) -> None:
        """Should return max(existing) + 1 for a new attempt."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_results.list_all = AsyncMock(
            return_value=[
                create_mock_result(1, "2024-03-15T09:00:00Z"),
                create_mock_result(2, "2024-03-15T09:30:00Z"),
            ]
        )

        attempt = await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",  # Different endedAt
        )

        assert attempt == 3

    @pytest.mark.asyncio
    async def test_reuses_attempt_for_retry_matching_score_date(self) -> None:
        """Should reuse attempt number when scoreDate matches (retry detection)."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_results.list_all = AsyncMock(
            return_value=[
                create_mock_result(1, "2024-03-15T09:00:00Z"),
                create_mock_result(2, "2024-03-15T10:30:00Z"),  # Same endedAt
            ]
        )

        attempt = await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",  # Matches result #2
        )

        assert attempt == 2

    @pytest.mark.asyncio
    async def test_reuses_attempt_for_retry_matching_metadata_ended_at(self) -> None:
        """Should reuse attempt when metadata.endedAt matches (retry detection)."""
        mock_client = MagicMock()
        result = {
            "sourcedId": "test-result",
            "status": "active",
            "assessmentLineItem": {"sourcedId": "line-item-1"},
            "student": {"sourcedId": "student-1"},
            "score": 80,
            "scoreDate": "different-date",  # scoreDate doesn't match
            "scoreStatus": "fully graded",
            "metadata": {
                "attempt": 3,
                "endedAt": "2024-03-15T10:30:00Z",  # But metadata.endedAt matches
            },
        }
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[result])

        attempt = await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",
        )

        assert attempt == 3

    @pytest.mark.asyncio
    async def test_handles_legacy_results_without_attempt(self) -> None:
        """Should handle legacy results without metadata.attempt."""
        mock_client = MagicMock()
        legacy_result = {
            "sourcedId": "legacy-result",
            "status": "active",
            "assessmentLineItem": {"sourcedId": "line-item-1"},
            "student": {"sourcedId": "student-1"},
            "score": 80,
            "scoreDate": "2024-03-15T10:30:00Z",
            "scoreStatus": "fully graded",
            "metadata": {},  # No attempt field
        }
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[legacy_result])

        # Retry of same endedAt should return 1 (fallback)
        retry_attempt = await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",
        )
        assert retry_attempt == 1

    @pytest.mark.asyncio
    async def test_filters_by_line_item_and_student(self) -> None:
        """Should filter by lineItem and student sourcedIds."""
        mock_client = MagicMock()
        mock_list_all = AsyncMock(return_value=[])
        mock_client.oneroster.assessment_results.list_all = mock_list_all

        await resolve_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",
        )

        mock_list_all.assert_called_once_with(
            where={
                "status": "active",
                "assessmentLineItem.sourcedId": "line-item-1",
                "student.sourcedId": "student-1",
            }
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test: write_gradebook_entry
# ─────────────────────────────────────────────────────────────────────────────


class TestWriteGradebookEntry:
    """Tests for write_gradebook_entry function."""

    @pytest.mark.asyncio
    async def test_skips_when_total_questions_missing(self) -> None:
        """Should skip when totalQuestions is missing."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()
        mock_client.oneroster.assessment_results = MagicMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"correctQuestions": 8},  # Missing totalQuestions
            pct_complete_app=None,
            app_name="Test App",
        )

        # Should not have made any API calls
        mock_client.oneroster.assessment_line_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_correct_questions_missing(self) -> None:
        """Should skip when correctQuestions is missing."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()
        mock_client.oneroster.assessment_results = MagicMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": 10},  # Missing correctQuestions
            pct_complete_app=None,
            app_name="Test App",
        )

        # Should not have made any API calls
        mock_client.oneroster.assessment_line_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_total_questions_is_zero(self) -> None:
        """Should skip when totalQuestions is 0 (avoid divide by zero)."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()
        mock_client.oneroster.assessment_results = MagicMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": 0, "correctQuestions": 0},
            pct_complete_app=None,
            app_name="Test App",
        )

        # Should not have made any API calls
        mock_client.oneroster.assessment_line_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_line_item_and_upserts_result(self) -> None:
        """Should create line item and upsert result when metrics are present."""
        mock_client = MagicMock()

        # Mock line item get to raise (not found)
        mock_line_item_get = AsyncMock(side_effect=Exception("Not found"))
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=mock_line_item_get)
        )
        mock_client.oneroster.assessment_line_items.create = AsyncMock()

        # Mock results - use update for upsert
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": 10, "correctQuestions": 8},
            pct_complete_app=50,
            app_name="Test App",
        )

        # Should have created line item
        mock_client.oneroster.assessment_line_items.create.assert_called_once()
        create_call = mock_client.oneroster.assessment_line_items.create.call_args[0][0]
        assert create_call["status"] == "active"
        assert create_call["course"]["sourcedId"] == "course-123"

        # Should have upserted result via update
        mock_client.oneroster.assessment_results.update.assert_called_once()
        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_id = update_args[0]
        result_payload = update_args[1]

        assert result_payload["score"] == 80  # 8/10 * 100
        assert result_payload["student"]["sourcedId"] == "student-456"

        # Result ID should include endedAt hash
        assert "attempt-1" in result_id
        assert ":e-" in result_id

    @pytest.mark.asyncio
    async def test_result_id_includes_ended_at_hash(self) -> None:
        """Result ID should include hashed endedAt to prevent concurrency collisions."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )

        # Mock results
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])
        mock_client.oneroster.assessment_results.update = AsyncMock()

        ended_at = "2024-03-15T10:30:00Z"
        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at=ended_at,
            metrics={"totalQuestions": 10, "correctQuestions": 8},
            pct_complete_app=None,
            app_name="Test App",
        )

        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_id = update_args[0]

        # Result ID should be: lineItemId:studentId:attempt-N:e-{hash}
        expected_hash = hash_suffix_64_base36(ended_at)
        assert result_id.endswith(f":e-{expected_hash}")
        # Full pattern check
        import re

        assert re.match(r"^.+:.+:attempt-\d+:e-[0-9a-z]+$", result_id)

    @pytest.mark.asyncio
    async def test_increments_attempt_for_new_submission(self) -> None:
        """Should use attempt number = max + 1 for new submission."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )

        # Mock existing results with attempts 1 and 2
        mock_client.oneroster.assessment_results.list_all = AsyncMock(
            return_value=[
                create_mock_result(1, "2024-03-15T09:00:00Z"),
                create_mock_result(2, "2024-03-15T09:30:00Z"),
            ]
        )
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",  # Different endedAt
            metrics={"totalQuestions": 10, "correctQuestions": 8},
            pct_complete_app=None,
            app_name="Test App",
        )

        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_id = update_args[0]
        result_payload = update_args[1]

        # Should be attempt 3
        assert "attempt-3" in result_id
        assert result_payload["metadata"]["attempt"] == 3

    @pytest.mark.asyncio
    async def test_reuses_attempt_for_retry(self) -> None:
        """Should reuse attempt number when endedAt matches (retry)."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )

        ended_at = "2024-03-15T10:30:00Z"
        # Mock existing result with same endedAt
        mock_client.oneroster.assessment_results.list_all = AsyncMock(
            return_value=[create_mock_result(2, ended_at)]
        )
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at=ended_at,  # Same endedAt as existing result
            metrics={"totalQuestions": 10, "correctQuestions": 8},
            pct_complete_app=None,
            app_name="Test App",
        )

        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_id = update_args[0]
        result_payload = update_args[1]

        # Should reuse attempt 2
        assert "attempt-2" in result_id
        assert result_payload["metadata"]["attempt"] == 2

    @pytest.mark.asyncio
    async def test_calculates_score_correctly(self) -> None:
        """Should calculate score as rounded percentage."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )

        # Mock results
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])
        mock_client.oneroster.assessment_results.update = AsyncMock()

        # Test 2/3 = 66.67 → rounds to 67
        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": 3, "correctQuestions": 2},
            pct_complete_app=None,
            app_name="Test App",
        )

        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_payload = update_args[1]
        assert result_payload["score"] == 67

    @pytest.mark.asyncio
    async def test_best_effort_continues_on_failure(self) -> None:
        """Should log and continue when gradebook write fails (best-effort)."""
        mock_client = MagicMock()

        # Mock line item get to raise (not found), then create to raise
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock(side_effect=Exception("Not found")))
        )
        mock_client.oneroster.assessment_line_items.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Should not raise - best-effort behavior
        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": 10, "correctQuestions": 8},
            pct_complete_app=None,
            app_name="Test App",
        )

        # Test passes if no exception is raised

    @pytest.mark.asyncio
    async def test_handles_string_metrics_without_raising(self) -> None:
        """Should not raise when metrics are strings instead of numbers (best-effort)."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()

        # Metrics as strings (e.g., from loose JSON parsing or form data)
        # This should NOT raise TypeError - function should handle gracefully
        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": "10", "correctQuestions": "8"},  # Strings!
            pct_complete_app=None,
            app_name="Test App",
        )

        # Test passes if no exception is raised (best-effort behavior)

    @pytest.mark.asyncio
    async def test_coerces_string_metrics_to_numbers(self) -> None:
        """Should coerce string metrics to numbers and compute score correctly."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )

        # Mock results
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": "10", "correctQuestions": "8"},  # Strings
            pct_complete_app=None,
            app_name="Test App",
        )

        # Should have written result with correct score
        mock_client.oneroster.assessment_results.update.assert_called_once()
        result_payload = mock_client.oneroster.assessment_results.update.call_args[0][1]
        assert result_payload["score"] == 80  # 8/10 * 100

    @pytest.mark.asyncio
    async def test_skips_when_metrics_are_non_numeric_strings(self) -> None:
        """Should skip gracefully when metrics are non-numeric strings."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()

        # Non-numeric strings should skip (can't compute score)
        await write_gradebook_entry(
            client=mock_client,
            course_id="course-123",
            activity_id="activity-123",
            activity_name="Test Activity",
            timeback_id="student-456",
            ended_at="2024-03-15T10:30:00Z",
            metrics={"totalQuestions": "abc", "correctQuestions": "def"},
            pct_complete_app=None,
            app_name="Test App",
        )

        # Should not have made any API calls (graceful skip)
        mock_client.oneroster.assessment_line_items.assert_not_called()
