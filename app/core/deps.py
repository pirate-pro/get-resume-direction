from typing import Any

from fastapi import Request

from app.core.config import Settings, get_settings
from app.middlewares.request_context import get_request_id, get_trace_id


def get_settings_dep() -> Settings:
    return get_settings()


def get_request_context(_: Request) -> dict[str, str]:
    return {
        "request_id": get_request_id(),
        "trace_id": get_trace_id(),
    }


async def get_current_user() -> dict[str, Any] | None:
    # Reserved for phase-2 auth integration.
    return None
