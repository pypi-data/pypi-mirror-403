"""Breadcrumbs module for Falcon SDK.

Captures events (HTTP requests, console logs, etc.) leading up to an error
for better debugging context.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger("falcon_sdk")

# =============================================================================
# Types
# =============================================================================

BreadcrumbType = Literal["http", "console", "click", "navigation", "custom"]


@dataclass
class Breadcrumb:
    """A breadcrumb event."""

    type: BreadcrumbType
    message: str
    category: str | None = None
    timestamp: str | None = None
    data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API payload."""
        return {
            "type": self.type,
            "category": self.category,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# =============================================================================
# Breadcrumb Buffer
# =============================================================================

MAX_BREADCRUMBS = 50

# Thread-safe breadcrumb storage
_breadcrumbs: deque[Breadcrumb] = deque(maxlen=MAX_BREADCRUMBS)
_lock = threading.Lock()
_max_breadcrumbs = MAX_BREADCRUMBS


def configure_breadcrumbs(max_breadcrumbs: int = MAX_BREADCRUMBS) -> None:
    """Configure the breadcrumbs buffer size."""
    global _breadcrumbs, _max_breadcrumbs
    with _lock:
        _max_breadcrumbs = max_breadcrumbs
        # Create new deque with new maxlen, preserving existing items
        old_items = list(_breadcrumbs)[-max_breadcrumbs:]
        _breadcrumbs = deque(old_items, maxlen=max_breadcrumbs)


def add_breadcrumb(
    type: BreadcrumbType,
    message: str,
    *,
    category: str | None = None,
    data: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> None:
    """
    Add a breadcrumb to the buffer.

    Args:
        type: Type of breadcrumb (http, console, click, navigation, custom)
        message: Description of the event
        category: Subcategory (e.g., 'fetch', 'xhr', 'log', 'warn')
        data: Additional context data
        timestamp: ISO format timestamp (defaults to now)

    Example:
        >>> add_breadcrumb(
        ...     type="custom",
        ...     message="User clicked checkout button",
        ...     category="ui.click",
        ...     data={"button_id": "checkout-btn"},
        ... )
    """
    breadcrumb = Breadcrumb(
        type=type,
        message=message,
        category=category,
        data=data,
        timestamp=timestamp,
    )

    with _lock:
        _breadcrumbs.append(breadcrumb)


def get_breadcrumbs() -> list[Breadcrumb]:
    """Get all breadcrumbs."""
    with _lock:
        return list(_breadcrumbs)


def clear_breadcrumbs() -> None:
    """Clear all breadcrumbs."""
    with _lock:
        _breadcrumbs.clear()


# =============================================================================
# Logging Integration
# =============================================================================


class BreadcrumbLoggingHandler(logging.Handler):
    """Logging handler that captures log messages as breadcrumbs.

    Example:
        >>> handler = BreadcrumbLoggingHandler()
        >>> logging.getLogger().addHandler(handler)
    """

    LEVEL_MAP = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warn",
        logging.ERROR: "error",
        logging.CRITICAL: "error",
    }

    def emit(self, record: logging.LogRecord) -> None:
        # Skip Falcon SDK's own logs
        if record.name.startswith("falcon_sdk"):
            return

        category = self.LEVEL_MAP.get(record.levelno, "log")

        add_breadcrumb(
            type="console",
            category=category,
            message=record.getMessage(),
            data={
                "logger": record.name,
                "level": record.levelname,
                "pathname": record.pathname,
                "lineno": record.lineno,
            }
            if record.pathname
            else None,
        )


# =============================================================================
# HTTP Request Instrumentation (httpx/requests)
# =============================================================================

_httpx_instrumented = False
_requests_instrumented = False


def instrument_httpx() -> None:
    """Instrument httpx to capture HTTP requests as breadcrumbs."""
    global _httpx_instrumented
    if _httpx_instrumented:
        return

    try:
        import httpx

        original_send = httpx.Client.send
        original_async_send = httpx.AsyncClient.send

        def wrapped_send(self: httpx.Client, request: httpx.Request, **kwargs: Any) -> httpx.Response:
            import time

            start_time = time.time()
            try:
                response = original_send(self, request, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url}",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url} (failed)",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        async def wrapped_async_send(
            self: httpx.AsyncClient, request: httpx.Request, **kwargs: Any
        ) -> httpx.Response:
            import time

            start_time = time.time()
            try:
                response = await original_async_send(self, request, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url}",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="httpx",
                    message=f"{request.method} {request.url} (failed)",
                    data={
                        "method": str(request.method),
                        "url": str(request.url),
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        httpx.Client.send = wrapped_send  # type: ignore
        httpx.AsyncClient.send = wrapped_async_send  # type: ignore

        _httpx_instrumented = True
        logger.debug("httpx instrumented for breadcrumbs")

    except ImportError:
        pass  # httpx not installed


def instrument_requests() -> None:
    """Instrument requests library to capture HTTP requests as breadcrumbs."""
    global _requests_instrumented
    if _requests_instrumented:
        return

    try:
        import requests

        original_request = requests.Session.request

        def wrapped_request(
            self: requests.Session, method: str, url: str, **kwargs: Any
        ) -> requests.Response:
            import time

            start_time = time.time()
            try:
                response = original_request(self, method, url, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="requests",
                    message=f"{method.upper()} {url}",
                    data={
                        "method": method.upper(),
                        "url": url,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="requests",
                    message=f"{method.upper()} {url} (failed)",
                    data={
                        "method": method.upper(),
                        "url": url,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        requests.Session.request = wrapped_request  # type: ignore

        _requests_instrumented = True
        logger.debug("requests instrumented for breadcrumbs")

    except ImportError:
        pass  # requests not installed


def instrument_aiohttp() -> None:
    """Instrument aiohttp to capture HTTP requests as breadcrumbs."""
    global _aiohttp_instrumented
    if _aiohttp_instrumented:
        return

    try:
        import aiohttp

        original_request = aiohttp.ClientSession._request

        async def wrapped_request(
            self: aiohttp.ClientSession, method: str, url: Any, **kwargs: Any
        ) -> aiohttp.ClientResponse:
            import time

            start_time = time.time()
            url_str = str(url)
            try:
                response = await original_request(self, method, url, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="aiohttp",
                    message=f"{method.upper()} {url_str}",
                    data={
                        "method": method.upper(),
                        "url": url_str,
                        "status_code": response.status,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="aiohttp",
                    message=f"{method.upper()} {url_str} (failed)",
                    data={
                        "method": method.upper(),
                        "url": url_str,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        aiohttp.ClientSession._request = wrapped_request  # type: ignore

        _aiohttp_instrumented = True
        logger.debug("aiohttp instrumented for breadcrumbs")

    except ImportError:
        pass  # aiohttp not installed


_aiohttp_instrumented = False


def instrument_urllib3() -> None:
    """Instrument urllib3 to capture HTTP requests as breadcrumbs."""
    global _urllib3_instrumented
    if _urllib3_instrumented:
        return

    try:
        import urllib3

        original_urlopen = urllib3.HTTPConnectionPool.urlopen

        def wrapped_urlopen(
            self: urllib3.HTTPConnectionPool, method: str, url: str, **kwargs: Any
        ) -> urllib3.HTTPResponse:
            import time

            start_time = time.time()
            full_url = f"{self.scheme}://{self.host}:{self.port}{url}"
            try:
                response = original_urlopen(self, method, url, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="urllib3",
                    message=f"{method.upper()} {full_url}",
                    data={
                        "method": method.upper(),
                        "url": full_url,
                        "status_code": response.status,
                        "duration_ms": duration_ms,
                    },
                )
                return response
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                add_breadcrumb(
                    type="http",
                    category="urllib3",
                    message=f"{method.upper()} {full_url} (failed)",
                    data={
                        "method": method.upper(),
                        "url": full_url,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    },
                )
                raise

        urllib3.HTTPConnectionPool.urlopen = wrapped_urlopen  # type: ignore

        _urllib3_instrumented = True
        logger.debug("urllib3 instrumented for breadcrumbs")

    except ImportError:
        pass  # urllib3 not installed


_urllib3_instrumented = False


def instrument_sqlalchemy() -> None:
    """Instrument SQLAlchemy to capture database queries as breadcrumbs."""
    global _sqlalchemy_instrumented
    if _sqlalchemy_instrumented:
        return

    try:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            import time

            conn.info.setdefault("query_start_time", time.time())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            import time

            start_time = conn.info.pop("query_start_time", time.time())
            duration_ms = int((time.time() - start_time) * 1000)

            # Extract operation type from statement
            operation = statement.strip().split()[0].upper() if statement.strip() else "QUERY"

            # Truncate long statements
            display_statement = statement[:200] + "..." if len(statement) > 200 else statement

            add_breadcrumb(
                type="custom",
                category="sql",
                message=f"{operation}: {display_statement}",
                data={
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "executemany": executemany,
                },
            )

        _sqlalchemy_instrumented = True
        logger.debug("SQLAlchemy instrumented for breadcrumbs")

    except ImportError:
        pass  # SQLAlchemy not installed


_sqlalchemy_instrumented = False


# =============================================================================
# Context Manager for Breadcrumb Scopes
# =============================================================================


class breadcrumb_scope:
    """Context manager that adds a breadcrumb when entering and exiting a scope.

    Example:
        >>> with breadcrumb_scope("checkout", category="user.action"):
        ...     process_payment()
        ...     update_inventory()

        >>> async with breadcrumb_scope("api_call", data={"endpoint": "/users"}):
        ...     await fetch_users()
    """

    def __init__(
        self,
        message: str,
        *,
        category: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.category = category
        self.data = data or {}
        self.start_time: float | None = None

    def __enter__(self) -> "breadcrumb_scope":
        import time

        self.start_time = time.time()
        add_breadcrumb(
            type="navigation",
            category=self.category or "scope",
            message=f"Enter: {self.message}",
            data=self.data,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        import time

        duration_ms = int((time.time() - (self.start_time or time.time())) * 1000)
        exit_data = {**self.data, "duration_ms": duration_ms}

        if exc_type is not None:
            exit_data["error"] = str(exc_val)
            add_breadcrumb(
                type="navigation",
                category=self.category or "scope",
                message=f"Exit (error): {self.message}",
                data=exit_data,
            )
        else:
            add_breadcrumb(
                type="navigation",
                category=self.category or "scope",
                message=f"Exit: {self.message}",
                data=exit_data,
            )

    async def __aenter__(self) -> "breadcrumb_scope":
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


def install_breadcrumb_integrations(
    *,
    http: bool = True,
    logging_handler: bool = True,
    logging_level: int = logging.INFO,
    sqlalchemy: bool = False,
) -> None:
    """
    Install automatic breadcrumb capture integrations.

    Args:
        http: Instrument HTTP libraries (httpx, requests, aiohttp, urllib3)
        logging_handler: Add a handler to the root logger
        logging_level: Minimum log level to capture
        sqlalchemy: Instrument SQLAlchemy for database query breadcrumbs
    """
    if http:
        instrument_httpx()
        instrument_requests()
        instrument_aiohttp()
        instrument_urllib3()

    if sqlalchemy:
        instrument_sqlalchemy()

    if logging_handler:
        handler = BreadcrumbLoggingHandler()
        handler.setLevel(logging_level)
        logging.getLogger().addHandler(handler)
        logger.debug(f"Installed breadcrumb logging handler (level={logging_level})")
