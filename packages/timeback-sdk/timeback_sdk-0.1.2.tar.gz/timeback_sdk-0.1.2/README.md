# Timeback SDK

Server-side SDK for integrating Timeback into Python web applications.

## Installation

```bash
# pip
pip install timeback-sdk[fastapi]
pip install timeback-sdk[django]

# uv (add to a project)
uv add "timeback-sdk[fastapi]"
uv add "timeback-sdk[django]"

# uv (install into current environment)
uv pip install "timeback-sdk[fastapi]"
uv pip install "timeback-sdk[django]"
```

## FastAPI

```python
from fastapi import FastAPI
from timeback.fastapi import create_timeback_router

app = FastAPI()

timeback_router = create_timeback_router(
    env="staging",
    client_id="...",
    client_secret="...",
    identity={
        "mode": "sso",
        "client_id": "...",
        "client_secret": "...",
        "get_user": lambda req: get_session_user(req),
        "on_callback_success": lambda ctx: handle_sso_success(ctx),
    },
)

app.include_router(timeback_router, prefix="/api/timeback")
```

## Django

```python
# Coming soon
```
