"""
Celery integration for Falcon error tracking.

Example:
    >>> from celery import Celery
    >>> from falcon_sdk import init
    >>> from falcon_sdk.celery import instrument_celery
    >>>
    >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-worker")
    >>> celery_app = Celery("tasks")
    >>>
    >>> # Instrument Celery for error tracking and auto-registration
    >>> instrument_celery(celery_app, falcon)
"""

from __future__ import annotations

import logging
from typing import Any

from .client import Falcon

logger = logging.getLogger("falcon_sdk.celery")


def instrument_celery(
    celery_app: Any,
    falcon: Falcon,
    *,
    auto_register: bool = True,
    capture_task_errors: bool = True,
) -> None:
    """
    Instrument a Celery app with Falcon error tracking and auto-registration.

    Args:
        celery_app: The Celery application instance
        falcon: The Falcon SDK instance
        auto_register: Auto-register app with Falcon on worker startup (default: True)
        capture_task_errors: Capture task failures as errors (default: True)

    Example:
        >>> from celery import Celery
        >>> from falcon_sdk import init
        >>> from falcon_sdk.celery import instrument_celery
        >>>
        >>> falcon = init(api_key="sk_falcon_xxx", app_name="my-worker")
        >>> celery_app = Celery("tasks")
        >>> instrument_celery(celery_app, falcon)
    """
    from celery.signals import (
        worker_ready,
        task_failure,
        task_retry,
    )

    # Register app when worker starts
    if auto_register:
        def on_worker_ready(sender: Any = None, **kwargs: Any) -> None:
            """Register with Falcon when worker is ready."""
            logger.info(f"[Falcon] Worker ready, registering app '{falcon.config.app_name}'")
            # Workers don't have health/metrics endpoints
            falcon.register_app(health_url=None, metrics_url=None)

        # Use weak=False to prevent garbage collection of the handler
        worker_ready.connect(on_worker_ready, weak=False)

    # Capture task failures
    if capture_task_errors:
        @task_failure.connect
        def on_task_failure(
            sender: Any = None,
            task_id: str | None = None,
            exception: BaseException | None = None,
            args: tuple | None = None,
            kwargs: dict | None = None,
            traceback: Any = None,
            einfo: Any = None,
            **extra: Any,
        ) -> None:
            """Capture task failures to Falcon."""
            if exception is None:
                return

            task_name = getattr(sender, "name", "unknown")
            context = {
                "celery": {
                    "task_id": task_id,
                    "task_name": task_name,
                    "args": _safe_repr(args),
                    "kwargs": _safe_repr(kwargs),
                }
            }

            falcon.capture_exception(
                exception,
                context=context,
                level="error",
            )
            logger.debug(f"[Falcon] Captured task failure: {task_name} ({task_id})")

        @task_retry.connect
        def on_task_retry(
            sender: Any = None,
            request: Any = None,
            reason: Any = None,
            einfo: Any = None,
            **extra: Any,
        ) -> None:
            """Capture task retries as warnings."""
            task_name = getattr(sender, "name", "unknown")
            task_id = getattr(request, "id", None) if request else None

            # Get the exception if available
            exception = None
            if einfo and hasattr(einfo, "exception"):
                exception = einfo.exception

            if exception:
                context = {
                    "celery": {
                        "task_id": task_id,
                        "task_name": task_name,
                        "retry_reason": str(reason) if reason else None,
                    }
                }

                falcon.capture_exception(
                    exception,
                    context=context,
                    level="warning",  # Retries are warnings, not errors
                )
                logger.debug(f"[Falcon] Captured task retry: {task_name} ({task_id})")


def _safe_repr(obj: Any, max_length: int = 200) -> str | None:
    """Safely convert object to string representation."""
    if obj is None:
        return None
    try:
        result = repr(obj)
        if len(result) > max_length:
            return result[:max_length] + "..."
        return result
    except Exception:
        return "<unrepresentable>"
