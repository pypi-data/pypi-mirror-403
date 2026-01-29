"""
Django adapter for Timeback SDK.

Provides URL patterns and views for Django integration.

Status: Not yet implemented. Coming soon.

Example (future API):
    ```python
    # urls.py
    from django.urls import path, include
    from timeback.django import get_timeback_urls

    urlpatterns = [
        path("api/timeback/", include(get_timeback_urls(
            env="staging",
            api={"client_id": "...", "client_secret": "..."},
            identity={"mode": "custom", "get_user": get_request_user},
        ))),
    ]
    ```
"""

# Django adapter implementation will be added when there's demand.
# Key considerations:
# - Django uses sync views by default (async views available in 3.1+)
# - Django has its own Request/Response objects (not Starlette)
# - Session handling is built-in via django.contrib.sessions
# - Authentication is built-in via django.contrib.auth
#
# Implementation approach:
# 1. Create view functions that wrap the core handlers
# 2. Convert Django HttpRequest to a common format
# 3. Convert handler responses back to Django HttpResponse
# 4. Provide both sync (using async_to_sync) and async views
