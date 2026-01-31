"""
Activity Attempt Resolution (for process: true)

Resolves attempt numbers for Caliper ActivityEvents when using `process: true`.

When `process: true` is set, timeback-api-2 creates assessment line items and results
using a specific ID format. This module computes the same line item ID so the SDK can
query existing results and determine the correct attempt number before sending the event.

Line Item ID formula (matches timeback-api-2's handleExternalUrl):
  `caliper_${sha256(objectId + "_" + courseSourcedId)}`

Attempt semantics:
- `attempt` is 1-based, stored in `metadata.attempt` on assessment results
- Retry detection: if `scoreDate` matches an existing result's `scoreDate`,
  the same attempt number is reused (idempotent retry)
- New attempt: if no matching `scoreDate` is found, attempt is `max(existingAttempt) + 1`
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...lib.logger import create_scoped_logger
from ...lib.utils import sha256_hex

if TYPE_CHECKING:
    from timeback_core import TimebackClient

log = create_scoped_logger("handlers:activity:attempts")


# ─────────────────────────────────────────────────────────────────────────────
# Line Item ID Computation
# ─────────────────────────────────────────────────────────────────────────────


def compute_caliper_line_item_id(object_id: str, course_sourced_id: str) -> str:
    """
    Compute the assessment line item sourcedId that timeback-api-2 creates for external URLs.

    This matches the logic in timeback-api-2's `handleExternalUrl` function:
    ```
    const idParts = [objectId, course.sourcedId].join("_")
    const hashedId = createHash("sha256").update(idParts).digest("hex")
    const sourcedId = `caliper_${hashedId}`
    ```
    """
    id_parts = f"{object_id}_{course_sourced_id}"
    return f"caliper_{sha256_hex(id_parts)}"


# ─────────────────────────────────────────────────────────────────────────────
# Attempt Resolution
# ─────────────────────────────────────────────────────────────────────────────


def _get_result_metadata(result: Any) -> dict[str, Any]:
    """
    Extract metadata from an assessment result.

    Handles both dict results and Pydantic model results.
    """
    if isinstance(result, dict):
        return result.get("metadata") or {}
    return getattr(result, "metadata", None) or {}


def _get_result_score_date(result: Any) -> str | None:
    """
    Extract scoreDate from an assessment result.

    Handles both dict results and Pydantic model results.
    """
    if isinstance(result, dict):
        return result.get("scoreDate") or result.get("score_date")
    return getattr(result, "score_date", None) or getattr(result, "scoreDate", None)


def _find_retry_result(existing_results: list[Any], ended_at: str) -> Any | None:
    """
    Find a previously-written result matching an endedAt timestamp.

    This enables idempotent retries for the same submission payload.
    timeback-api-2 uses `scoreDate` to store the activity's endedAt.
    """
    for result in existing_results:
        score_date = _get_result_score_date(result)
        if score_date == ended_at:
            return result
    return None


def _compute_max_attempt(existing_results: list[Any]) -> int:
    """Compute the maximum attempt number present in result metadata."""
    max_attempt = 0
    for result in existing_results:
        metadata = _get_result_metadata(result)
        attempt = metadata.get("attempt")
        if isinstance(attempt, int) and attempt > max_attempt:
            max_attempt = attempt
    return max_attempt


def _resolve_attempt_from_result(result: Any) -> int:
    """
    Resolve a usable attempt number from a result.

    Treats missing/invalid attempt metadata as attempt 1 (legacy support).
    """
    metadata = _get_result_metadata(result)
    attempt = metadata.get("attempt")
    return attempt if isinstance(attempt, int) and attempt >= 1 else 1


async def resolve_caliper_attempt_number(
    client: TimebackClient,
    line_item_id: str,
    timeback_id: str,
    ended_at: str,
) -> int:
    """
    Resolve the attempt number for a Caliper ActivityEvent.

    This queries assessment results created by timeback-api-2 to determine
    the correct attempt number before sending the Caliper event.

    - If an existing result has `scoreDate` matching the payload, return its attempt (retry).
    - Otherwise, return `max(metadata.attempt) + 1` (new attempt).
    """
    try:
        existing_results = await client.oneroster.assessment_results.list_all(
            where={
                "status": "active",
                "assessmentLineItem.sourcedId": line_item_id,
                "student.sourcedId": timeback_id,
            }
        )
    except Exception:
        # If fetching fails (e.g., 404 because line item doesn't exist yet), assume first attempt
        log.debug(
            "No existing results found (line item may not exist yet): line_item_id=%s",
            line_item_id,
        )
        return 1

    if len(existing_results) == 0:
        # No existing results → first attempt
        return 1

    # Check for retry (same endedAt timestamp)
    retry_result = _find_retry_result(existing_results, ended_at)

    if retry_result is not None:
        attempt = _resolve_attempt_from_result(retry_result)
        log.debug(
            "Retry detected, reusing attempt number: line_item_id=%s, timeback_id=%s, attempt=%d",
            line_item_id,
            timeback_id,
            attempt,
        )
        return attempt

    # No retry found — compute new attempt number
    max_attempt = _compute_max_attempt(existing_results)
    next_attempt = max_attempt + 1

    log.debug(
        "New attempt computed: line_item_id=%s, timeback_id=%s, max_attempt=%d, next_attempt=%d",
        line_item_id,
        timeback_id,
        max_attempt,
        next_attempt,
    )

    return next_attempt
