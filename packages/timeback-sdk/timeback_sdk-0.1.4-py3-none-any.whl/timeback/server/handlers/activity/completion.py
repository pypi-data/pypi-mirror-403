"""
Mastery Completion Entry

Creates a special "mastery-completion" line item + result when course mastery is achieved.
This line item IS connected to `componentResource`, which triggers course completion
on dashboards — unlike regular activity line items which intentionally omit the link
to prevent premature completion.

@see Playcademy's MasteryTracker.createCompletionEntry for the original pattern
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ...lib.logger import create_scoped_logger
from ...lib.utils import derive_course_structure_ids, sha256_hex

if TYPE_CHECKING:
    from timeback_core import TimebackClient

log = create_scoped_logger("handlers:activity:completion")


async def maybe_write_completion_entry(
    *,
    client: TimebackClient,
    course_id: str,
    timeback_id: str,
    pct_complete: int | None,
    app_name: str,
) -> None:
    """
    Create a mastery completion entry if the student has achieved 100% completion.

    This is a workaround for OneRoster/dashboard completion detection:
    - Regular line items are NOT connected to the component resource
      (to prevent the first fully-graded result from marking the course complete)
    - This special "mastery-completion" line item IS connected to the component resource
    - When mastery is achieved (pctComplete === 100), we create this line item + a fully graded result
    - This triggers course completion while allowing XP to aggregate normally

    XXX: errors are logged but do not fail the overall request.
    """
    if pct_complete != 100:
        return

    ids = derive_course_structure_ids(course_id)

    line_item_id = f"timeback_sdk_{sha256_hex(f'mastery-completion_{course_id}')}"
    result_id = f"timeback_sdk_{sha256_hex(f'mastery-completion_{course_id}_{timeback_id}')}"

    try:
        line_item_exists = False

        try:
            await client.oneroster.assessment_line_items(line_item_id).get()
            line_item_exists = True
        except Exception:
            # Line item doesn't exist, will create below
            pass

        if not line_item_exists:
            # Create the "Mastery Completion" line item, tying the student's progress to
            # a specific component resource within the course. This completion line item
            # is special in that it is explicitly linked to the componentResource entity.
            #
            # Linking the line item in this way is essential: it enables the OneRoster
            # dashboard to recognize and register completion of the course, as opposed
            # to regular line items that are kept separate to avoid prematurely marking
            # the course as finished. Only when a student achieves 100% completion,
            # this special line item is written, which serves as the definitive trigger
            # for course completion while still allowing XP and partial progress to
            # accumulate on other assessments as usual.
            await client.oneroster.assessment_line_items.create(
                {
                    "sourcedId": line_item_id,
                    "title": f"{app_name}: Complete",
                    "status": "active",
                    "course": {"sourcedId": ids.course},
                    "componentResource": {"sourcedId": ids.component_resource},
                    "resultValueMin": 0,
                    "resultValueMax": 100,
                    "metadata": {"appName": app_name},
                }
            )

        now = datetime.now(UTC).isoformat()

        await client.oneroster.assessment_results.update(
            result_id,
            {
                "sourcedId": result_id,
                "status": "active",
                "assessmentLineItem": {"sourcedId": line_item_id},
                "student": {"sourcedId": timeback_id},
                "score": 100,
                "scoreDate": now,
                "scoreStatus": "fully graded",
                "metadata": {
                    "isMasteryCompletion": True,
                    "completedAt": now,
                    "appName": app_name,
                },
            },
        )

        log.debug(
            "Created mastery completion entry: course_id=%s, timeback_id=%s, line_item_id=%s, result_id=%s",
            course_id,
            timeback_id,
            line_item_id,
            result_id,
        )

    except Exception as err:
        message = str(err) if err else "Unknown error"
        log.error(
            "Failed to create mastery completion entry: course_id=%s, timeback_id=%s, line_item_id=%s, error=%s",
            course_id,
            timeback_id,
            line_item_id,
            message,
        )
