from typing import Any

from app.middlewares.request_context import get_request_id


def success_response(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "request_id": get_request_id(),
        "data": data,
    }


def error_response(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "request_id": get_request_id(),
        "data": data,
    }
