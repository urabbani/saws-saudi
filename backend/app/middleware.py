"""
SAWS Middleware Components

Custom middleware for:
- CORS handling
- Request logging
- Error handling
- Security headers
- Request timing
"""

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings

settings = get_settings()


def setup_cors(app: FastAPI) -> None:
    """
    Setup CORS middleware.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Total-Count", "X-Page-Size"],
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to each request.

    Adds:
    - X-Request-ID header for tracing
    - Request timing
    - Request logging
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add request state
        request.state.request_id = request_id
        request.state.start_time = time.time()

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        # Calculate processing time
        process_time = time.time() - request.state.start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers.

    Adds:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (in production)
    - Content-Security-Policy
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS only in production with HTTPS
        if settings.environment == "production":
            hsts_max_age = 31536000  # 1 year
            response.headers["Strict-Transport-Security"] = f"max-age={hsts_max_age}; includeSubDomains"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging.

    Logs:
    - Request method and path
    - Response status code
    - Processing time
    - Client IP
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import structlog

        logger = structlog.get_logger()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip,
            request_id=request_id,
        )

        # Process request
        try:
            response = await call_next(request)

            # Get process time
            process_time = getattr(request.state, "start_time", time.time())
            duration = time.time() - process_time

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                request_id=request_id,
            )

            return response

        except Exception as e:
            # Get process time
            process_time = getattr(request.state, "start_time", time.time())
            duration = time.time() - process_time

            # Log error
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                request_id=request_id,
            )
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.

    Catches all exceptions and returns formatted JSON responses.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": f"HTTP_{e.status_code}",
                        "message": e.detail,
                    }
                },
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(e),
                    }
                },
            )
        except PermissionError as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": str(e),
                    }
                },
            )
        except Exception as e:
            # Log the error
            import structlog

            logger = structlog.get_logger()
            logger.exception(
                "unhandled_exception",
                path=request.url.path,
                method=request.method,
                error=str(e),
            )

            # Return generic error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                    }
                    if settings.debug
                    else {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
                }


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the application.

    Args:
        app: FastAPI application instance
    """
    setup_cors(app)

    # Order matters - add middleware in reverse order of execution
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
