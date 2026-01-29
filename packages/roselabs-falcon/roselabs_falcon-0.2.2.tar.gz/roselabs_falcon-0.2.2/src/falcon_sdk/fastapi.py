"""
FastAPI middleware for Falcon error tracking.

Example:
    >>> from fastapi import FastAPI
    >>> from falcon_sdk import init
    >>> from falcon_sdk.fastapi import instrument_fastapi
    >>>
    >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
    >>> app = FastAPI()
    >>>
    >>> # Full instrumentation with auto health/metrics (registers on first request)
    >>> instrument_fastapi(app, falcon, auto_uptime=True, auto_metrics=True)
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse, JSONResponse
from starlette.types import ASGIApp

from .client import Falcon
from .health import create_health_response, DEFAULT_HEALTH_PATH
from .metrics import format_prometheus, record_request, DEFAULT_METRICS_PATH
from .types import UserContext

# Type for user extractor callback
UserExtractor = Callable[[Request], UserContext | Awaitable[UserContext | None] | None]


class FalconMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware that captures unhandled exceptions.

    Also handles lazy app registration on first request if base_url
    was not provided during instrumentation.

    Usage:
        app.add_middleware(FalconMiddleware, falcon=falcon_instance)
    """

    def __init__(
        self,
        app: ASGIApp,
        falcon: Falcon,
        collect_metrics: bool = False,
        *,
        # Registration config (for lazy registration on first request)
        auto_register: bool = False,
        health_path: str | None = None,
        metrics_path: str | None = None,
        user_extractor: UserExtractor | None = None,
    ) -> None:
        super().__init__(app)
        self.falcon = falcon
        self.collect_metrics = collect_metrics
        self._auto_register = auto_register
        self._health_path = health_path
        self._metrics_path = metrics_path
        self._registered = False
        self._user_extractor = user_extractor

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Lazy registration on first request (if needed)
        if self._auto_register and not self._registered:
            await self._register_from_request(request)

        # Extract user context if extractor provided
        user: UserContext | None = None
        if self._user_extractor:
            try:
                result = self._user_extractor(request)
                # Handle async extractors
                if hasattr(result, "__await__"):
                    user = await result
                else:
                    user = result
            except Exception:
                pass  # Don't fail request if user extraction fails

        try:
            response = await call_next(request)

            # Record request metrics if enabled
            if self.collect_metrics:
                duration_ms = (time.time() - start_time) * 1000
                record_request(request.method, response.status_code, duration_ms)

            return response
        except Exception as exc:
            # Record failed request
            if self.collect_metrics:
                duration_ms = (time.time() - start_time) * 1000
                record_request(request.method, 500, duration_ms)

            # Set user context temporarily for this exception
            old_user = self.falcon._user
            if user:
                self.falcon._user = user

            try:
                # Capture the exception with request context
                await self.falcon.capture_exception_async(
                    exc,
                    context=_build_request_context(request, start_time, user),
                    level="error",
                )
            finally:
                # Restore previous user context
                self.falcon._user = old_user

            # Re-raise so FastAPI's exception handlers can process it
            raise

    async def _register_from_request(self, request: Request) -> None:
        """Register app using the request's host to build URLs."""
        self._registered = True  # Mark as registered (even if it fails, don't retry)

        # Build base URL from request
        # Prefer X-Forwarded-Proto/Host headers (for reverse proxies like nginx)
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))

        if not host:
            return  # Can't determine URL

        base_url = f"{scheme}://{host}"

        health_url = f"{base_url}{self._health_path}" if self._health_path else None
        metrics_url = f"{base_url}{self._metrics_path}" if self._metrics_path else None

        await self.falcon.register_app_async(
            health_url=health_url,
            metrics_url=metrics_url,
        )


def instrument_fastapi(
    app: ASGIApp,
    falcon: Falcon,
    *,
    auto_uptime: bool = False,
    auto_metrics: bool = False,
    auto_register: bool = True,
    base_url: str | None = None,
    health_path: str = DEFAULT_HEALTH_PATH,
    metrics_path: str = DEFAULT_METRICS_PATH,
    health_check: Callable[[], bool | Awaitable[bool]] | None = None,
    version: str | None = None,
    user_extractor: UserExtractor | None = None,
) -> None:
    """
    Instrument a FastAPI app with Falcon error tracking and optional health/metrics.

    Args:
        app: The FastAPI application instance
        falcon: The Falcon SDK instance
        auto_uptime: Auto-register health check endpoint (default: False)
        auto_metrics: Auto-register metrics endpoint (default: False)
        auto_register: Auto-register app with Falcon on first request (default: True)
        base_url: Base URL for health/metrics endpoints. If not provided:
                  1. Uses FALCON_PUBLIC_URL env var if set
                  2. Falls back to detecting from first request's Host header
        health_path: Custom health check path (default: /__falcon/health)
        metrics_path: Custom metrics path (default: /__falcon/metrics)
        health_check: Custom health check function (sync or async)
        version: Application version to report in health check
        user_extractor: Optional callback to extract user from request for error tracking.
                       Should return UserContext or None. Can be sync or async.
                       Example: lambda req: UserContext(id=req.state.user_id, email=req.state.email)

    Example:
        >>> from fastapi import FastAPI
        >>> from falcon_sdk import init, UserContext
        >>> from falcon_sdk.fastapi import instrument_fastapi
        >>>
        >>> app = FastAPI()
        >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
        >>>
        >>> # Auto-register on first request (recommended)
        >>> instrument_fastapi(app, falcon, auto_uptime=True, auto_metrics=True)
        >>>
        >>> # With user tracking from JWT
        >>> def extract_user(request):
        ...     if hasattr(request.state, "user"):
        ...         return UserContext(id=request.state.user.id, email=request.state.user.email)
        ...     return None
        >>>
        >>> instrument_fastapi(app, falcon, user_extractor=extract_user)
    """
    # Get app name from Falcon config
    app_name = falcon.config.app_name if hasattr(falcon, "config") else None

    # Add health endpoint if enabled
    if auto_uptime:
        async def health_endpoint(request: Request) -> JSONResponse:
            response, status_code = await create_health_response(
                app_name=app_name,
                version=version,
                check=health_check,
            )
            return JSONResponse(content=response.to_dict(), status_code=status_code)

        # Add route to the app
        from starlette.routing import Route
        app.routes.insert(0, Route(health_path, health_endpoint, methods=["GET"]))  # type: ignore

    # Add metrics endpoint if enabled
    if auto_metrics:
        async def metrics_endpoint(request: Request) -> PlainTextResponse:
            output = format_prometheus()
            return PlainTextResponse(
                content=output,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        from starlette.routing import Route
        app.routes.insert(0, Route(metrics_path, metrics_endpoint, methods=["GET"]))  # type: ignore

    # Determine registration strategy
    should_register_now = False
    should_register_lazy = False
    health_url: str | None = None
    metrics_url: str | None = None

    if auto_register:
        # Priority 1: Explicit base_url parameter
        if base_url:
            should_register_now = True
            health_url = f"{base_url.rstrip('/')}{health_path}" if auto_uptime else None
            metrics_url = f"{base_url.rstrip('/')}{metrics_path}" if auto_metrics else None

        # Priority 2: FALCON_PUBLIC_URL environment variable
        elif os.environ.get("FALCON_PUBLIC_URL"):
            public_url = os.environ["FALCON_PUBLIC_URL"].rstrip("/")
            should_register_now = True
            health_url = f"{public_url}{health_path}" if auto_uptime else None
            metrics_url = f"{public_url}{metrics_path}" if auto_metrics else None

        # Priority 3: Lazy registration on first request
        else:
            should_register_lazy = True

    # Register now if we have the URL
    if should_register_now:
        # Use background registration to avoid blocking startup
        from threading import Thread
        Thread(
            target=falcon.register_app,
            kwargs={"health_url": health_url, "metrics_url": metrics_url},
            daemon=True,
        ).start()

    # Add error tracking middleware (with lazy registration if needed)
    app.add_middleware(  # type: ignore
        FalconMiddleware,
        falcon=falcon,
        collect_metrics=auto_metrics,
        auto_register=should_register_lazy,
        health_path=health_path if auto_uptime else None,
        metrics_path=metrics_path if auto_metrics else None,
        user_extractor=user_extractor,
    )


def create_exception_handler(falcon: Falcon):
    """
    Create a FastAPI exception handler that reports to Falcon.

    Use this if you want to handle specific exception types while still
    reporting them to Falcon.

    Example:
        >>> from fastapi import FastAPI, HTTPException
        >>> from falcon_sdk import init
        >>> from falcon_sdk.fastapi import create_exception_handler
        >>>
        >>> app = FastAPI()
        >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-app")
        >>>
        >>> @app.exception_handler(Exception)
        >>> async def handle_exception(request, exc):
        ...     handler = create_exception_handler(falcon)
        ...     return await handler(request, exc)
    """

    async def exception_handler(request: Request, exc: Exception) -> Response:
        # Capture to Falcon
        await falcon.capture_exception_async(
            exc,
            context=_build_request_context(request),
            level="error",
        )

        # Return a generic error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return exception_handler


def _build_request_context(
    request: Request,
    start_time: float | None = None,
    user: UserContext | None = None,
) -> dict[str, Any]:
    """Build context dict from a Starlette/FastAPI request."""
    context: dict[str, Any] = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_string": request.url.query,
            "headers": _sanitize_headers(dict(request.headers)),
            "client": request.client.host if request.client else None,
        }
    }

    if start_time:
        context["duration_ms"] = round((time.time() - start_time) * 1000, 2)

    # Add path parameters if available
    if hasattr(request, "path_params") and request.path_params:
        context["request"]["path_params"] = dict(request.path_params)

    # Add user info to context
    if user:
        context["user"] = user.to_dict()

    return context


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers before sending to Falcon."""
    sensitive = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
    }
    return {
        k: "[REDACTED]" if k.lower() in sensitive else v for k, v in headers.items()
    }
