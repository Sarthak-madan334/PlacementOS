"""Standardized exceptions and handlers for PlacementOS."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base application exception with stable error code and status."""

    def __init__(
        self,
        detail: str,
        code: str = "app_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.headers = headers
        super().__init__(detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Authentication required", code: str = "unauthorized"):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Permission denied", code: str = "forbidden"):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", code: str = "not_found"):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationException(AppException):
    def __init__(self, detail: str, code: str = "validation_error"):
        super().__init__(
            detail=detail,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers returning {"detail": "...", "code": "..."}."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "http_error"
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "unauthorized"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "forbidden"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
        elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            code = "validation_error"
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            code = "service_unavailable"

        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "code": code},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Format validation error messages cleanly
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}")
        detail_msg = "; ".join(errors) if errors else "Invalid request payload"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": detail_msg,
                "code": "validation_error",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never expose internal stack traces or database errors in responses
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred",
                "code": "internal_error",
            },
        )
