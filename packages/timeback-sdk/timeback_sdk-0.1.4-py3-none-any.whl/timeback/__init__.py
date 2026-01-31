"""
Timeback SDK for Python.

Server-side SDK for integrating Timeback into Python web applications.

Example (FastAPI with SSO - Full SDK):
    ```python
    from fastapi import FastAPI
    from timeback import ApiCredentials, SsoIdentityConfig
    from timeback.server import create_server, to_fastapi_router

    async def create_app():
        timeback = await create_server(TimebackConfig(
            env="staging",
            api=ApiCredentials(
                client_id=os.environ["TIMEBACK_API_CLIENT_ID"],
                client_secret=os.environ["TIMEBACK_API_CLIENT_SECRET"],
            ),
            identity=SsoIdentityConfig(
                mode="sso",
                client_id=os.environ["COGNITO_CLIENT_ID"],
                client_secret=os.environ["COGNITO_CLIENT_SECRET"],
                get_user=get_session_user,  # returns { id: timebackId, email }
                on_callback_success=handle_sso_success,
            ),
        ))

        app = FastAPI()
        app.include_router(to_fastapi_router(timeback), prefix="/api/timeback")
        return app
    ```

Example (FastAPI with custom auth):
    ```python
    from timeback import ApiCredentials, CustomIdentityConfig
    from timeback.server import create_server, to_fastapi_router

    timeback = await create_server(TimebackConfig(
        env="staging",
        api=ApiCredentials(client_id="...", client_secret="..."),
        identity=CustomIdentityConfig(
            mode="custom",
            get_email=lambda req: get_session(req).email,  # returns email string
        ),
    ))
    ```

Example (FastAPI with SSO - Identity-Only):
    ```python
    from fastapi import FastAPI
    from timeback import IdentityOnlyConfig, IdentityOnlySsoConfig
    from timeback.server import create_identity_only_server, to_fastapi_router

    timeback = create_identity_only_server(IdentityOnlyConfig(
        env="staging",
        identity=IdentityOnlySsoConfig(
            mode="sso",
            client_id=os.environ["COGNITO_CLIENT_ID"],
            client_secret=os.environ["COGNITO_CLIENT_SECRET"],
            on_callback_success=lambda ctx: ctx.redirect("/dashboard"),
        ),
    ))

    app = FastAPI()
    app.include_router(to_fastapi_router(timeback), prefix="/api/auth")
    ```
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("timeback-sdk")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .server.types import (
    ApiCredentials,
    BuildStateContext,
    CallbackErrorContext,
    CallbackSuccessContext,
    CustomIdentityConfig,
    IdentityConfig,
    IdentityOnlyCallbackSuccessContext,
    IdentityOnlyConfig,
    IdentityOnlySsoConfig,
    IdpData,
    OIDCTokens,
    OIDCUserInfo,
    SsoIdentityConfig,
    TimebackConfig,
)
from .shared.types import (
    ActivityCourseRef,
    ActivityEndPayload,
    ActivityMetrics,
    ActivityParams,
    ActivityResponse,
    CourseCodeRef,
    Environment,
    IdentityClaims,
    SubjectGradeCourseRef,
    TimebackAuthUser,
    TimebackIdentity,
    TimebackProfile,
    TimebackSessionUser,
    TimebackUser,
    TimebackUserResolutionErrorCode,
    is_subject_grade_course_ref,
)

__all__ = [
    "ActivityCourseRef",
    "ActivityEndPayload",
    "ActivityMetrics",
    "ActivityParams",
    "ActivityResponse",
    "ApiCredentials",
    "BuildStateContext",
    "CallbackErrorContext",
    "CallbackSuccessContext",
    "CourseCodeRef",
    "CustomIdentityConfig",
    "Environment",
    "IdentityClaims",
    "IdentityConfig",
    "IdentityOnlyCallbackSuccessContext",
    "IdentityOnlyConfig",
    "IdentityOnlySsoConfig",
    "IdpData",
    "OIDCTokens",
    "OIDCUserInfo",
    "SsoIdentityConfig",
    "SubjectGradeCourseRef",
    "TimebackAuthUser",
    "TimebackConfig",
    "TimebackIdentity",
    "TimebackProfile",
    "TimebackSessionUser",
    "TimebackUser",
    "TimebackUserResolutionErrorCode",
    "__version__",
    "is_subject_grade_course_ref",
]
