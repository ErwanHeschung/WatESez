"""Translates domain exceptions into HTTP responses.

Keeps status-code knowledge at the HTTP boundary so services stay framework
agnostic and the worker can catch the same exceptions without FastAPI.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    AudioDecodeError,
    FingerprintError,
    JobNotFoundError,
    LyricsNotFoundError,
    QueueFullError,
    SeparationError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_EXCEPTION = {
    JobNotFoundError: status.HTTP_404_NOT_FOUND,
    LyricsNotFoundError: status.HTTP_404_NOT_FOUND,
    QueueFullError: status.HTTP_429_TOO_MANY_REQUESTS,
    AudioDecodeError: status.HTTP_400_BAD_REQUEST,
    FingerprintError: 422,
    SeparationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exc_type, _make_handler(status_code))


def _make_handler(status_code: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        if status_code >= 500:
            logger.exception("Unhandled domain error on %s", request.url.path)
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler
