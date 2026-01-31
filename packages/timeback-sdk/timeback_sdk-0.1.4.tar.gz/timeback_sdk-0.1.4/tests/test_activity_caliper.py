"""Tests for activity Caliper-driven gradebook functionality.

With the new flow, the SDK no longer writes gradebook entries directly.
Instead, Caliper events are sent with process=True, and timeback-api-2
handles gradebook creation. The SDK only writes a special "mastery completion"
entry when pctComplete reaches 100%.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from timeback.server.handlers.activity import (
    compute_caliper_line_item_id,
    maybe_write_completion_entry,
    resolve_caliper_attempt_number,
)
from timeback.server.handlers.activity.caliper import build_activity_context
from timeback.server.lib.utils import sha256_hex
from timeback.shared.types import SubjectGradeCourseRef

# ─────────────────────────────────────────────────────────────────────────────
# Test: process=True in activity context
# ─────────────────────────────────────────────────────────────────────────────


class TestActivityContextProcessFlag:
    """Tests for process=True in activity context builder."""

    _OR_BASE_URL = "https://api.example.com"
    _OR_ROSTERING_PATH = "/ims/oneroster/rostering/v1p2"

    def test_activity_context_has_process_true(self) -> None:
        """Activity context should have process=True (Caliper-driven gradebook)."""
        course_config = {
            "subject": "Math",
            "grade": 3,
            "ids": {"staging": "course-123"},
        }

        context = build_activity_context(
            activity_id="lesson-123",
            activity_name="Test Lesson",
            course_selector=SubjectGradeCourseRef(subject="Math", grade=3),
            course_config=course_config,
            app_name="Test App",
            api_env="staging",
            sensor="https://sensor.example.com",
            oneroster_base_url=self._OR_BASE_URL,
            oneroster_rostering_path=self._OR_ROSTERING_PATH,
        )

        assert context.process is True


# ─────────────────────────────────────────────────────────────────────────────
# Test: compute_caliper_line_item_id
# ─────────────────────────────────────────────────────────────────────────────


class TestComputeCaliperLineItemId:
    """Tests for Caliper-style line item ID computation."""

    def test_computes_deterministic_id(self) -> None:
        """Should compute a deterministic line item ID from object_id and course_id."""
        object_id = "https://sensor.example.com/activities/Math/g3/fractions"
        course_id = "course-123"

        line_item_id = compute_caliper_line_item_id(object_id, course_id)

        # Should be prefixed with 'caliper_'
        assert line_item_id.startswith("caliper_")
        # Should be a sha256 hash
        expected_hash = sha256_hex(f"{object_id}_{course_id}")
        assert line_item_id == f"caliper_{expected_hash}"

    def test_different_inputs_produce_different_ids(self) -> None:
        """Different inputs should produce different line item IDs."""
        id1 = compute_caliper_line_item_id("activity-1", "course-1")
        id2 = compute_caliper_line_item_id("activity-2", "course-1")
        id3 = compute_caliper_line_item_id("activity-1", "course-2")

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3


# ─────────────────────────────────────────────────────────────────────────────
# Test: resolve_caliper_attempt_number
# ─────────────────────────────────────────────────────────────────────────────


def create_mock_result(attempt: int, score_date: str) -> dict[str, Any]:
    """Create a mock assessment result for testing."""
    return {
        "sourcedId": f"result-{attempt}",
        "status": "active",
        "assessmentLineItem": {"sourcedId": "test-line-item"},
        "student": {"sourcedId": "student-456"},
        "score": 80,
        "scoreDate": score_date,
        "scoreStatus": "fully graded",
        "metadata": {
            "attempt": attempt,
        },
    }


class TestResolveCaliperAttemptNumber:
    """Tests for resolve_caliper_attempt_number function."""

    @pytest.mark.asyncio
    async def test_returns_1_when_no_existing_results(self) -> None:
        """Should return 1 when there are no existing results."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_results.list_all = AsyncMock(return_value=[])

        attempt = await resolve_caliper_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",
        )

        assert attempt == 1

    @pytest.mark.asyncio
    async def test_returns_1_when_fetch_fails(self) -> None:
        """Should return 1 when API call fails (e.g., line item doesn't exist yet)."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_results.list_all = AsyncMock(
            side_effect=Exception("404 Not Found")
        )

        attempt = await resolve_caliper_attempt_number(
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

        attempt = await resolve_caliper_attempt_number(
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

        attempt = await resolve_caliper_attempt_number(
            mock_client,
            "line-item-1",
            "student-1",
            "2024-03-15T10:30:00Z",  # Matches result #2
        )

        assert attempt == 2

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
        retry_attempt = await resolve_caliper_attempt_number(
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

        await resolve_caliper_attempt_number(
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
# Test: maybe_write_completion_entry
# ─────────────────────────────────────────────────────────────────────────────


class TestMaybeWriteCompletionEntry:
    """Tests for maybe_write_completion_entry function."""

    @pytest.mark.asyncio
    async def test_does_nothing_when_pct_complete_is_none(self) -> None:
        """Should do nothing when pct_complete is None."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()
        mock_client.oneroster.assessment_results = MagicMock()

        await maybe_write_completion_entry(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            pct_complete=None,
            app_name="Test App",
        )

        # Should not have made any API calls
        mock_client.oneroster.assessment_line_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_nothing_when_pct_complete_is_less_than_100(self) -> None:
        """Should do nothing when pct_complete < 100."""
        mock_client = MagicMock()
        mock_client.oneroster.assessment_line_items = MagicMock()
        mock_client.oneroster.assessment_results = MagicMock()

        await maybe_write_completion_entry(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            pct_complete=99,
            app_name="Test App",
        )

        # Should not have made any API calls
        mock_client.oneroster.assessment_line_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_line_item_and_result_when_pct_complete_is_100(self) -> None:
        """Should create completion line item and result when pct_complete == 100."""
        mock_client = MagicMock()

        # Mock line item get to raise (not found)
        mock_line_item_get = AsyncMock(side_effect=Exception("Not found"))
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=mock_line_item_get)
        )
        mock_client.oneroster.assessment_line_items.create = AsyncMock()
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await maybe_write_completion_entry(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            pct_complete=100,
            app_name="Test App",
        )

        # Should have created line item
        mock_client.oneroster.assessment_line_items.create.assert_called_once()
        create_call = mock_client.oneroster.assessment_line_items.create.call_args[0][0]
        assert create_call["status"] == "active"
        assert create_call["course"]["sourcedId"] == "course-123"
        assert create_call["componentResource"]["sourcedId"] == "course-123-cr"
        assert create_call["title"] == "Test App: Complete"

        # Should have upserted result via update
        mock_client.oneroster.assessment_results.update.assert_called_once()
        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        result_payload = update_args[1]

        assert result_payload["score"] == 100
        assert result_payload["scoreStatus"] == "fully graded"
        assert result_payload["student"]["sourcedId"] == "student-456"
        assert result_payload["metadata"]["isMasteryCompletion"] is True

    @pytest.mark.asyncio
    async def test_uses_deterministic_ids(self) -> None:
        """Should use deterministic IDs based on course and student."""
        mock_client = MagicMock()

        # Mock line item exists
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock())
        )
        mock_client.oneroster.assessment_results.update = AsyncMock()

        course_id = "course-123"
        timeback_id = "student-456"

        await maybe_write_completion_entry(
            client=mock_client,
            course_id=course_id,
            timeback_id=timeback_id,
            pct_complete=100,
            app_name="Test App",
        )

        # Verify line item ID
        expected_line_item_id = f"timeback_sdk_{sha256_hex(f'mastery-completion_{course_id}')}"
        mock_client.oneroster.assessment_line_items.assert_called_with(expected_line_item_id)

        # Verify result ID
        expected_result_id = (
            f"timeback_sdk_{sha256_hex(f'mastery-completion_{course_id}_{timeback_id}')}"
        )
        update_args = mock_client.oneroster.assessment_results.update.call_args[0]
        assert update_args[0] == expected_result_id

    @pytest.mark.asyncio
    async def test_skips_line_item_creation_if_exists(self) -> None:
        """Should not create line item if it already exists."""
        mock_client = MagicMock()

        # Mock line item exists (get succeeds)
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock(return_value={}))
        )
        mock_client.oneroster.assessment_line_items.create = AsyncMock()
        mock_client.oneroster.assessment_results.update = AsyncMock()

        await maybe_write_completion_entry(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            pct_complete=100,
            app_name="Test App",
        )

        # Should NOT have created line item (it already exists)
        mock_client.oneroster.assessment_line_items.create.assert_not_called()

        # Should still have upserted result
        mock_client.oneroster.assessment_results.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_best_effort_continues_on_failure(self) -> None:
        """Should log and continue when completion write fails (best-effort)."""
        mock_client = MagicMock()

        # Mock line item get to raise (not found), then create to raise
        mock_client.oneroster.assessment_line_items = MagicMock(
            return_value=MagicMock(get=AsyncMock(side_effect=Exception("Not found")))
        )
        mock_client.oneroster.assessment_line_items.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Should not raise - best-effort behavior
        await maybe_write_completion_entry(
            client=mock_client,
            course_id="course-123",
            timeback_id="student-456",
            pct_complete=100,
            app_name="Test App",
        )

        # Test passes if no exception is raised
