"""
Activity Gradebook (OneRoster)

Write assessment line items and results for activity submissions.

Attempt semantics:
- `attempt` is the primary identity (1-based) stored in `metadata.attempt`
- Results are **created** by `(lineItem, student, attempt)` and **updated** on retry
- Retry detection: if `payload.endedAt` matches an existing result's `scoreDate` (and `metadata.endedAt`),
  the same attempt number is reused to make retries idempotent
- New attempt: if no matching `endedAt` is found, attempt is `max(existingAttempt) + 1`

Concurrency note:
- Two concurrent "new attempts" for the same (lineItem, student) can race.
- We avoid silent overwrites by including `endedAt` in the result ID, so two distinct
  submissions never share an ID even if they compute the same attempt number concurrently.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ...lib.logger import create_scoped_logger
from ...lib.utils import hash_suffix_64_base36, safe_id_segment

if TYPE_CHECKING:
    from timeback_core import TimebackClient

log = create_scoped_logger("handlers:activity:gradebook")


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


def _get_result_sourced_id(result: Any) -> str | None:
    """
    Extract sourcedId from an assessment result.

    Handles both dict results and Pydantic model results.
    """
    if isinstance(result, dict):
        return result.get("sourcedId") or result.get("sourced_id")
    return getattr(result, "sourced_id", None) or getattr(result, "sourcedId", None)


def _find_retry_result(existing_results: list[Any], ended_at: str) -> Any | None:
    """
    Find an existing result that matches the given endedAt timestamp.

    A match indicates this is a retry of the same attempt.
    """
    for result in existing_results:
        metadata = _get_result_metadata(result)
        score_date = _get_result_score_date(result)
        score_date_matches = score_date == ended_at
        metadata_ended_at_matches = metadata.get("endedAt") == ended_at

        if score_date_matches or metadata_ended_at_matches:
            return result
    return None


def _compute_max_attempt(existing_results: list[Any]) -> int:
    """Compute the maximum attempt number from existing results."""
    max_attempt = 0
    for result in existing_results:
        metadata = _get_result_metadata(result)
        attempt = metadata.get("attempt")
        if isinstance(attempt, int) and attempt > max_attempt:
            max_attempt = attempt
    return max_attempt


def _resolve_attempt_from_result(result: Any) -> int:
    """Extract the attempt number from a result, defaulting to 1."""
    metadata = _get_result_metadata(result)
    attempt = metadata.get("attempt")
    return attempt if isinstance(attempt, int) and attempt >= 1 else 1


async def _resolve_attempt_info(
    client: TimebackClient,
    line_item_id: str,
    timeback_id: str,
    ended_at: str,
) -> tuple[int, Any | None]:
    """
    Resolve attempt info for a gradebook result.

    - If an existing result has `scoreDate === endedAt` or `metadata.endedAt === endedAt`,
      return its `metadata.attempt` and the existing result (retry).
    - Otherwise, return `max(metadata.attempt) + 1` and None (new attempt).

    Args:
        client: Timeback client
        line_item_id: The assessment line item sourcedId
        timeback_id: The student's Timeback user sourcedId
        ended_at: The activity end timestamp from the client payload

    Returns:
        (attempt_number, retry_result) - retry_result is the existing result if this is a retry, else None
    """
    existing_results = await client.oneroster.assessment_results.list_all(
        where={
            "status": "active",
            "assessmentLineItem.sourcedId": line_item_id,
            "student.sourcedId": timeback_id,
        }
    )

    if len(existing_results) == 0:
        # No existing results → first attempt
        return (1, None)

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
        return (attempt, retry_result)

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

    return (next_attempt, None)


async def resolve_attempt_number(
    client: TimebackClient,
    line_item_id: str,
    timeback_id: str,
    ended_at: str,
) -> int:
    """
    Resolve the attempt number for a gradebook result.

    - If an existing result has `scoreDate === endedAt` or `metadata.endedAt === endedAt`,
      return its `metadata.attempt` (retry of the same attempt).
    - Otherwise, return `max(metadata.attempt) + 1` (new attempt).

    Args:
        client: Timeback client
        line_item_id: The assessment line item sourcedId
        timeback_id: The student's Timeback user sourcedId
        ended_at: The activity end timestamp from the client payload

    Returns:
        The attempt number to use (1-based)
    """
    attempt, _ = await _resolve_attempt_info(client, line_item_id, timeback_id, ended_at)
    return attempt


# ─────────────────────────────────────────────────────────────────────────────
# Gradebook Write
# ─────────────────────────────────────────────────────────────────────────────


def _build_attempt_result_id(
    line_item_id: str, timeback_id: str, attempt: int, ended_at: str
) -> str:
    """
    Build a deterministic attempt-based assessment result sourcedId.

    Includes a hash of endedAt in the ID to prevent collisions under concurrency -
    two distinct submissions never share an ID even if they compute the
    same attempt number concurrently.

    Args:
        line_item_id: Assessment line item sourcedId
        timeback_id: Student sourcedId
        attempt: Attempt number (1-based)
        ended_at: End timestamp (hashed to prevent collisions under concurrency)

    Returns:
        Attempt-based result sourcedId
    """
    return f"{line_item_id}:{safe_id_segment(timeback_id)}:attempt-{attempt}:e-{hash_suffix_64_base36(ended_at)}"


def _build_assessment_result_payload(
    *,
    result_id: str,
    line_item_id: str,
    timeback_id: str,
    attempt: int,
    score: int,
    ended_at: str,
    metrics: dict[str, Any],
    pct_complete_app: int | None,
    app_name: str,
) -> dict[str, Any]:
    """Build the assessment result payload."""
    return {
        "sourcedId": result_id,
        "status": "active",
        "assessmentLineItem": {"sourcedId": line_item_id},
        "student": {"sourcedId": timeback_id},
        "score": score,
        "scoreDate": ended_at,
        "scoreStatus": "fully graded",
        "inProgress": "false",
        "metadata": {
            "totalQuestions": metrics.get("totalQuestions"),
            "correctQuestions": metrics.get("correctQuestions"),
            "accuracy": score,
            "xpEarned": metrics.get("xpEarned"),
            "masteredUnits": metrics.get("masteredUnits"),
            "attempt": attempt,
            "endedAt": ended_at,
            "pctCompleteApp": pct_complete_app,
            "appName": app_name,
            "lastUpdated": datetime.now(UTC).isoformat(),
        },
    }


async def _ensure_assessment_line_item_exists(
    client: TimebackClient,
    line_item_id: str,
    activity_name: str,
    course_id: str,
    app_name: str,
) -> None:
    """Ensure the assessment line item exists, creating it if needed."""
    try:
        await client.oneroster.assessment_line_items(line_item_id).get()
        return  # Exists
    except Exception:
        # Doesn't exist → create below
        pass

    try:
        await client.oneroster.assessment_line_items.create(
            {
                "sourcedId": line_item_id,
                "title": activity_name,
                "status": "active",
                "course": {"sourcedId": course_id},
                "resultValueMin": 0,
                "resultValueMax": 100,
                "metadata": {
                    "createdBy": "timeback-sdk",
                    "appName": app_name,
                },
            }
        )
    except Exception as err:
        # Concurrency safety: if two requests race on line item creation, one may fail
        # with "already exists". If the line item now exists, proceed.
        try:
            await client.oneroster.assessment_line_items(line_item_id).get()
        except Exception:
            raise err

    log.debug("Created assessment line item: %s", line_item_id)


async def _write_assessment_result(
    client: TimebackClient,
    line_item_id: str,
    timeback_id: str,
    score: int,
    ended_at: str,
    metrics: dict[str, Any],
    pct_complete_app: int | None,
    app_name: str,
) -> None:
    """
    Write an assessment result with optimistic concurrency for attempt numbers.

    - If `endedAt` matches an existing result, update that result (retry).
    - Otherwise, upsert a new result with `attempt = max + 1`.

    The result ID includes `endedAt`, so two distinct submissions never share an ID
    even if they compute the same attempt number concurrently.
    """
    attempt, retry_result = await _resolve_attempt_info(client, line_item_id, timeback_id, ended_at)

    # For retries, reuse the existing result's sourcedId if available
    if retry_result is not None:
        result_id = _get_result_sourced_id(retry_result) or _build_attempt_result_id(
            line_item_id, timeback_id, attempt, ended_at
        )
    else:
        # New attempt: include endedAt in the resultId so two distinct submissions
        # never share an ID even if they compute the same attempt number concurrently.
        result_id = _build_attempt_result_id(line_item_id, timeback_id, attempt, ended_at)

    payload = _build_assessment_result_payload(
        result_id=result_id,
        line_item_id=line_item_id,
        timeback_id=timeback_id,
        attempt=attempt,
        score=score,
        ended_at=ended_at,
        metrics=metrics,
        pct_complete_app=pct_complete_app,
        app_name=app_name,
    )

    await client.oneroster.assessment_results.update(result_id, payload)

    log.debug(
        "Wrote gradebook entry (%s): line_item_id=%s, result_id=%s, score=%d, attempt=%d",
        "retry" if retry_result else "new attempt",
        line_item_id,
        result_id,
        score,
        attempt,
    )


def _coerce_to_number(value: Any) -> int | float | None:
    """
    Coerce a value to a number (int or float).

    Returns None if the value cannot be converted.
    """
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        try:
            # Try int first, then float
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return None
    return None


async def write_gradebook_entry(
    *,
    client: TimebackClient,
    course_id: str,
    activity_id: str,
    activity_name: str,
    timeback_id: str,
    ended_at: str,
    metrics: dict[str, Any],
    pct_complete_app: int | None,
    app_name: str,
) -> None:
    """
    Write gradebook entry (assessment line item + result) for an activity.

    This is best-effort: if the write fails, we log and continue.
    Gradebook writes are only performed when both totalQuestions and correctQuestions are present.

    Result identity is based on attempt number and endedAt:
    - `resultId = lineItemId:studentId:attempt-N:endedAt-{encodedTimestamp}`
    - Retries of the same attempt (same `endedAt`) reuse the same result ID
    - New attempts get an incremented attempt number

    Args:
        client: Timeback client
        course_id: The course sourcedId
        activity_id: The activity ID/slug
        activity_name: The activity display name
        timeback_id: The student's Timeback user sourcedId
        ended_at: The activity end timestamp (ISO 8601)
        metrics: Activity metrics from the payload
        pct_complete_app: Optional app completion percentage
        app_name: The application name
    """
    # Only write to gradebook when we can compute a valid score
    raw_total = metrics.get("totalQuestions")
    raw_correct = metrics.get("correctQuestions")

    if raw_total is None or raw_correct is None:
        log.debug(
            "Skipping gradebook write: missing totalQuestions or correctQuestions, activity_id=%s",
            activity_id,
        )
        return

    # Coerce to numbers (handles string metrics gracefully)
    total_questions = _coerce_to_number(raw_total)
    correct_questions = _coerce_to_number(raw_correct)

    if total_questions is None or correct_questions is None:
        log.debug(
            "Skipping gradebook write: non-numeric totalQuestions or correctQuestions, activity_id=%s",
            activity_id,
        )
        return

    # Skip if totalQuestions is 0 or negative (avoid divide-by-zero / invalid data)
    if total_questions <= 0:
        log.debug(
            "Skipping gradebook write: totalQuestions must be positive, activity_id=%s, totalQuestions=%s",
            activity_id,
            total_questions,
        )
        return

    # Calculate score and clamp to 0-100 range
    raw_score = (correct_questions / total_questions) * 100
    score = round(min(100, max(0, raw_score)))

    line_item_id = f"{safe_id_segment(course_id)}-{safe_id_segment(activity_id)}-assessment"

    try:
        # 1. Ensure assessment line item exists
        await _ensure_assessment_line_item_exists(
            client,
            line_item_id,
            activity_name,
            course_id,
            app_name,
        )

        # 2. Write assessment result
        await _write_assessment_result(
            client,
            line_item_id,
            timeback_id,
            score,
            ended_at,
            metrics,
            pct_complete_app,
            app_name,
        )
    except Exception as err:
        message = str(err) if err else "Unknown error"
        log.warning(
            "Failed to write gradebook entry: line_item_id=%s, error=%s", line_item_id, message
        )
