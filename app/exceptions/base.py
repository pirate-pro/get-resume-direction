import logging
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.response import error_response
from app.exceptions import codes

logger = logging.getLogger(__name__)


@dataclass
class BusinessError(Exception):
    biz_code: int
    message: str
    http_status: int = 400
    data: Any = None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def handle_business_error(_: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=error_response(code=exc.biz_code, message=exc.message, data=exc.data),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_response(
                code=codes.INTERNAL_ERROR,
                message="Internal server error",
                data={"detail": str(exc)},
            ),
        )
