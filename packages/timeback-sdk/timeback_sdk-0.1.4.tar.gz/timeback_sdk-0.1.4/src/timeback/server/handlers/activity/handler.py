"""
Activity Handler

HTTP route handler for activity submissions.
Orchestrates validation, user resolution, gradebook writes, and Caliper event sending.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, cast

from starlette.responses import JSONResponse, Response

from timeback_caliper import TimebackUser
from timeback_common import ValidationError as CaliperValidationError
from timeback_core import TimebackClient

from ....shared.xp_calculator import calculate_xp
from ...lib.logger import create_scoped_logger
from ...lib.resolve import (
    TimebackUserResolutionError,
    lookup_timeback_id_by_email,
    resolve_status_for_user_resolution_error,
)
from ...lib.utils import map_env_for_api
from ...types import (
    ActivityBeforeSendData,
    ActivityHandlerDeps,
    ActivityUserInfo,
    CustomIdentityConfig,
    ValidatedActivityPayload,
    ValidationError,
)
from .attempts import compute_caliper_line_item_id, resolve_caliper_attempt_number
from .caliper import (
    InvalidSensorUrlError,
    MissingSyncedCourseIdError,
    build_activity_context,
    build_activity_events,
    build_activity_metrics,
    build_canonical_activity_url,
    build_oneroster_user_url,
    build_time_spent_metrics,
)
from .completion import maybe_write_completion_entry as maybe_write_completion_entry_impl
from .progress import compute_progress as compute_progress_impl
from .schema import format_course_selector, validate_activity_request

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

    from ...timeback import AppConfig
    from ...types import ApiCredentials, Environment, IdentityConfig, TimebackHooks

log = create_scoped_logger("handlers:activity")


# ─────────────────────────────────────────────────────────────────────────────
# Default Dependencies
# ─────────────────────────────────────────────────────────────────────────────

_default_deps = ActivityHandlerDeps(
    compute_progress=compute_progress_impl,
    maybe_write_completion_entry=maybe_write_completion_entry_impl,
)


# ─────────────────────────────────────────────────────────────────────────────
# User Resolution
# ─────────────────────────────────────────────────────────────────────────────


async def _get_activity_user_info(
    identity: IdentityConfig,
    request: Request,
) -> ActivityUserInfo | None:
    """
    Get user info from the request based on identity mode.

    - SSO mode: returns email + timebackId (from session, no lookup needed)
    - Custom mode: returns email only (lookup required)
    """
    if isinstance(identity, CustomIdentityConfig) or identity.mode == "custom":
        get_email = identity.get_email
        if not get_email:
            return None

        result = get_email(request)
        email = await result if inspect.isawaitable(result) else result
        return ActivityUserInfo(email=email) if email else None

    get_user = identity.get_user
    if not get_user:
        return None

    result = get_user(request)
    user = await result if inspect.isawaitable(result) else result
    return ActivityUserInfo(email=user.email, timeback_id=user.id) if user else None


async def _resolve_timeback_id(user_info: ActivityUserInfo, client: TimebackClient) -> str:
    """Resolve the timebackId, using cached value from SSO or looking up by email."""
    if user_info.timeback_id:
        return user_info.timeback_id
    return await lookup_timeback_id_by_email(email=user_info.email, client=client)


# ─────────────────────────────────────────────────────────────────────────────
# Auto XP Calculation
# ─────────────────────────────────────────────────────────────────────────────


async def _resolve_attempt_and_maybe_auto_xp(
    *,
    client: TimebackClient,
    body: dict[str, Any],
    payload: ValidatedActivityPayload,
    timeback_id: str,
    synced_course_id: str,
    object_id: str,
    preview_requested: bool,
) -> tuple[dict[str, Any], int]:
    """
    Resolve attempt number and auto-calculate xpEarned when omitted.

    When process: true, timeback-api-2 creates assessment results using a
    deterministic line item ID. We query existing results to determine the
    correct attempt number before sending the event.

    Auto-XP priority: explicit xpEarned > calculated from duration/accuracy/attempt > omit
    """
    metrics = body.get("metrics", {})
    has_total = metrics.get("totalQuestions") is not None
    has_correct = metrics.get("correctQuestions") is not None
    should_auto_calculate = metrics.get("xpEarned") is None and has_total and has_correct

    attempt_number = 1
    if not preview_requested:
        line_item_id = compute_caliper_line_item_id(object_id, synced_course_id)
        attempt_number = await resolve_caliper_attempt_number(
            client, line_item_id, timeback_id, body.get("endedAt", "")
        )

    if not should_auto_calculate:
        return body, attempt_number

    total_questions = metrics["totalQuestions"]
    correct_questions = metrics["correctQuestions"]
    duration_seconds = body.get("elapsedMs", 0) / 1000
    accuracy = correct_questions / total_questions if total_questions > 0 else float("nan")
    xp_earned = calculate_xp(duration_seconds, accuracy, attempt_number)

    updated_body = {**body, "metrics": {**metrics, "xpEarned": xp_earned}}
    payload.metrics = {**payload.metrics, "xpEarned": xp_earned}

    return updated_body, attempt_number


# ─────────────────────────────────────────────────────────────────────────────
# Preview Response
# ─────────────────────────────────────────────────────────────────────────────


def _build_preview_response(data: ActivityBeforeSendData) -> Response:
    """Build preview response with built events (not sent)."""
    return JSONResponse(
        {
            "success": True,
            "preview": True,
            "sensor": data.sensor,
            "actor": data.actor,
            "object": data.object.model_dump(by_alias=True)
            if hasattr(data.object, "model_dump")
            else data.object,
            "events": [
                e.model_dump(by_alias=True) if hasattr(e, "model_dump") else e for e in data.events
            ],
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Error Handling
# ─────────────────────────────────────────────────────────────────────────────


def _map_error_to_response(err: Exception, payload: ValidatedActivityPayload) -> Response:
    """Map known errors to appropriate HTTP responses."""
    selector_desc = format_course_selector(payload.course)

    if isinstance(err, TimebackUserResolutionError):
        log.warning("Failed to resolve Timeback user: %s", err.code)
        return JSONResponse(
            {"success": False, "error": "Unable to resolve Timeback identity"},
            status_code=resolve_status_for_user_resolution_error(err),
        )

    if isinstance(err, MissingSyncedCourseIdError):
        log.error("Course not synced: %s, env=%s", err.course, err.env)
        return JSONResponse({"success": False, "error": str(err)}, status_code=500)

    if isinstance(err, InvalidSensorUrlError):
        log.error("Invalid sensor URL: %s", err.sensor)
        return JSONResponse({"success": False, "error": str(err)}, status_code=502)

    if isinstance(err, CaliperValidationError):
        log.error(
            "Caliper validation error: course=%s, id=%s, error=%s",
            selector_desc,
            payload.id,
            str(err),
        )
        return JSONResponse(
            {"success": False, "error": str(err), "details": err.response}, status_code=502
        )

    log.error(
        "Failed to submit activity: course=%s, id=%s, error=%s", selector_desc, payload.id, str(err)
    )
    return JSONResponse({"success": False, "error": str(err)}, status_code=502)


# ─────────────────────────────────────────────────────────────────────────────
# Handler
# ─────────────────────────────────────────────────────────────────────────────


def create_activity_handler(
    *,
    env: Environment,
    api: ApiCredentials,
    identity: IdentityConfig,
    app_config: AppConfig,
    hooks: TimebackHooks | None = None,
    deps: ActivityHandlerDeps = _default_deps,
) -> Callable[[Request], Awaitable[Response]]:
    """Create the activity POST handler."""
    api_env = map_env_for_api(env)

    async def handler(request: Request) -> Response:
        preview_requested = (
            request.query_params.get("preview") == "1"
            or request.headers.get("x-timeback-preview") == "1"
        )

        # ═══════════════════════════════════════════════════════════════════════
        # Step 1: Authenticate
        # ═══════════════════════════════════════════════════════════════════════
        user_info = await _get_activity_user_info(identity, request)
        if not user_info:
            return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)

        # ═══════════════════════════════════════════════════════════════════════
        # Step 2: Validate request
        # ═══════════════════════════════════════════════════════════════════════
        body = await request.json()
        result = validate_activity_request(body, app_config)

        if isinstance(result, ValidationError):
            return result.response

        payload = result.payload
        course_config = result.course
        sensor = result.sensor

        # ═══════════════════════════════════════════════════════════════════════
        # Step 3: Verify course is synced for this environment
        # ═══════════════════════════════════════════════════════════════════════
        synced_course_id = (course_config.get("ids") or {}).get(api_env)
        if not isinstance(synced_course_id, str) or not synced_course_id:
            raise MissingSyncedCourseIdError(course_config, api_env)

        # ═══════════════════════════════════════════════════════════════════════
        # Step 4: Initialize client and resolve user
        # ═══════════════════════════════════════════════════════════════════════
        client = TimebackClient(
            env=api_env, client_id=api.client_id, client_secret=api.client_secret
        )

        try:
            timeback_id = await _resolve_timeback_id(user_info, client)
            effective_body = body

            # ═══════════════════════════════════════════════════════════════════
            # Step 5: Compute pctComplete if not provided by client
            #
            # Uses EduBridge enrollment analytics to aggregate historical mastered
            # units, then combines with the current submission's mastered units.
            # ═══════════════════════════════════════════════════════════════════
            if body.get("pctComplete") is None:
                computed_pct = await deps.compute_progress(
                    client=client,
                    course_id=synced_course_id,
                    timeback_id=timeback_id,
                    payload=body,
                    course_config=course_config,
                    env=env,
                )
                if computed_pct is not None:
                    effective_body = {**body, "pctComplete": computed_pct}

            # ═══════════════════════════════════════════════════════════════════
            # Step 6: Resolve attempt number and auto-calculate XP
            #
            # When process: true, timeback-api-2 creates assessment results using
            # a deterministic line item ID. We query existing results to determine
            # the correct attempt number before sending the event.
            #
            # The attempt number is also used for XP diminishing returns.
            # ═══════════════════════════════════════════════════════════════════
            object_id = build_canonical_activity_url(sensor, payload.course, payload.id)
            effective_body, attempt_number = await _resolve_attempt_and_maybe_auto_xp(
                client=client,
                body=effective_body,
                payload=payload,
                timeback_id=timeback_id,
                synced_course_id=synced_course_id,
                object_id=object_id,
                preview_requested=preview_requested,
            )

            # ═══════════════════════════════════════════════════════════════════
            # Step 7: Build Caliper events
            # ═══════════════════════════════════════════════════════════════════
            or_transport = client.oneroster.get_transport()
            oneroster_base_url = cast("str", getattr(or_transport, "base_url", None))
            if not oneroster_base_url:
                raise RuntimeError("OneRoster base_url is not configured")

            oneroster_rostering_path = cast(
                "str",
                getattr(
                    getattr(or_transport, "paths", None),
                    "rostering",
                    "/ims/oneroster/rostering/v1p2",
                ),
            )

            actor = TimebackUser(
                id=build_oneroster_user_url(
                    base_url=oneroster_base_url,
                    rostering_path=oneroster_rostering_path,
                    user_sourced_id=timeback_id,
                ),
                type="TimebackUser",
                email=user_info.email,
            )

            activity_context = build_activity_context(
                activity_id=payload.id,
                activity_name=payload.name,
                course_selector=payload.course,
                course_config=course_config,
                app_name=app_config.name,
                api_env=api_env,
                sensor=sensor,
                oneroster_base_url=oneroster_base_url,
                oneroster_rostering_path=oneroster_rostering_path,
            )

            activity_metrics = build_activity_metrics(payload.metrics)
            time_spent_metrics = build_time_spent_metrics(payload.elapsed_ms, payload.paused_ms)

            # Extensions for generated metrics (pctCompleteApp)
            generated_extensions: dict[str, object] | None = None
            pct_complete = effective_body.get("pctComplete")
            if pct_complete is not None:
                generated_extensions = {"pctCompleteApp": pct_complete}

            # Top-level event extensions (courseId for server-side filtering)
            event_extensions: dict[str, object] = {"courseId": synced_course_id}

            activity_event, time_spent_event = build_activity_events(
                actor=actor,
                activity_context=activity_context,
                activity_metrics=activity_metrics,
                time_spent_metrics=time_spent_metrics,
                event_time=payload.ended_at,
                attempt=attempt_number if attempt_number > 0 else None,
                generated_extensions=generated_extensions,
                event_extensions=event_extensions,
            )

            # ═══════════════════════════════════════════════════════════════════
            # Step 8: Run beforeActivitySend hook
            # ═══════════════════════════════════════════════════════════════════
            built_data = ActivityBeforeSendData(
                sensor=sensor,
                actor={"id": actor.id, "type": actor.type, "email": actor.email},
                object=activity_context,
                events=(activity_event, time_spent_event),
                payload=effective_body,
                course=course_config,
                app_name=app_config.name,
                api_env=api_env,
                email=user_info.email,
                timeback_id=timeback_id,
            )

            hook_result = built_data
            if hooks and hooks.before_activity_send:
                hook_fn = hooks.before_activity_send
                result = hook_fn(built_data)
                hook_result = await result if inspect.isawaitable(result) else result

            effective_data = hook_result if hook_result is not None else built_data

            # ═══════════════════════════════════════════════════════════════════
            # Step 9: Preview mode — return events without sending
            #
            # - preview_requested: explicit request via query param or header
            # - hook_result is None: hook chose to skip send (demo/test)
            # ═══════════════════════════════════════════════════════════════════
            skip_send = preview_requested or hook_result is None
            if skip_send:
                return _build_preview_response(effective_data)

            # ═══════════════════════════════════════════════════════════════════
            # Step 10: Send Caliper events
            #
            # With process: true, timeback-api-2 handles gradebook writes via
            # xp_transactions. Regular line items are NOT connected to the
            # component resource (to prevent premature completion).
            # ═══════════════════════════════════════════════════════════════════
            await client.caliper.events.send(effective_data.sensor, list(effective_data.events))

            # ═══════════════════════════════════════════════════════════════════
            # Step 11: Write mastery completion entry if pctComplete is 100
            #
            # This special line item triggers course completion on dashboards.
            # Unlike regular line items, it IS connected to componentResource.
            # ═══════════════════════════════════════════════════════════════════
            await deps.maybe_write_completion_entry(
                client=client,
                course_id=synced_course_id,
                timeback_id=effective_data.timeback_id,
                pct_complete=effective_data.payload.get("pctComplete"),
                app_name=effective_data.app_name,
            )

            selector_desc = format_course_selector(payload.course)
            log.debug("Submitted activity: course=%s, id=%s", selector_desc, payload.id)

            return JSONResponse({"success": True})

        except (
            TimebackUserResolutionError,
            MissingSyncedCourseIdError,
            InvalidSensorUrlError,
            CaliperValidationError,
        ) as e:
            return _map_error_to_response(e, payload)

        except Exception as e:
            return _map_error_to_response(e, payload)

        finally:
            await client.close()

    return handler
