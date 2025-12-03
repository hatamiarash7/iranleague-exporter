"""Main module for the Iran League exporter."""

from __future__ import annotations

import asyncio
import logging
import secrets
import signal
import sys
import threading
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    Info,
    generate_latest,
)
from starlette.responses import JSONResponse, Response

from iranleague_exporter import __version__
from iranleague_exporter.config import get_config
from iranleague_exporter.crawler import CrawlerError, get_matches

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Application state
_shutdown_event = asyncio.Event()
_last_update_time: datetime | None = None
_last_update_success: bool = False
_last_error: str | None = None

background_tasks: set[asyncio.Task] = set()
security = HTTPBasic()
log = logging.getLogger("uvicorn.error")

# Prometheus registry and metrics
registry = CollectorRegistry()

matches_gauge = Gauge(
    "ir_league_matches",
    "Timestamp of IR football league matches",
    ["teams"],
    registry=registry,
)

exporter_info = Info(
    "ir_league_exporter",
    "Information about the Iran League exporter",
    registry=registry,
)

scrape_duration_gauge = Gauge(
    "ir_league_scrape_duration_seconds",
    "Duration of the last scrape in seconds",
    registry=registry,
)

scrape_success_gauge = Gauge(
    "ir_league_scrape_success",
    "Whether the last scrape was successful (1) or not (0)",
    registry=registry,
)

matches_count_gauge = Gauge(
    "ir_league_matches_total",
    "Total number of future matches found",
    registry=registry,
)

metric_lock = threading.Lock()


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Verify the provided basic-auth credential.

    Args:
        credentials: Provided credential.

    Returns:
        Username if credentials are valid.

    Raises:
        HTTPException: If credentials are incorrect.
    """
    config = get_config()

    correct_username = secrets.compare_digest(
        credentials.username,
        config.auth.username,
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        config.auth.password,
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def update_metrics() -> None:
    """Fetch match data and update the Prometheus metrics."""
    global _last_update_time, _last_update_success, _last_error

    config = get_config()
    log.info("Updating metrics")
    start_time = datetime.now(UTC)

    try:
        matches = get_matches(config.label_lang)
        log.debug("Got %d matches", len(matches))

        with metric_lock:
            # Clear existing match metrics
            matches_gauge.clear()
            count = 0

            # Update metrics with new data
            for match in matches:
                teams = match.get("teams")
                timestamp = match.get("timestamp")
                if teams is not None and timestamp is not None:
                    matches_gauge.labels(teams=teams).set(timestamp)
                    count += 1

            # Update meta metrics
            duration = (datetime.now(UTC) - start_time).total_seconds()
            scrape_duration_gauge.set(duration)
            scrape_success_gauge.set(1)
            matches_count_gauge.set(count)

            _last_update_time = datetime.now(UTC)
            _last_update_success = True
            _last_error = None

        log.debug("Updated %d metrics in %.2f seconds", count, duration)

    except CrawlerError as e:
        log.error("Crawler error while updating metrics: %s", e)
        with metric_lock:
            scrape_success_gauge.set(0)
            duration = (datetime.now(UTC) - start_time).total_seconds()
            scrape_duration_gauge.set(duration)

        _last_update_time = datetime.now(UTC)
        _last_update_success = False
        _last_error = str(e)

    except Exception as e:
        log.exception("Unexpected error updating metrics: %s", e)
        with metric_lock:
            scrape_success_gauge.set(0)
            duration = (datetime.now(UTC) - start_time).total_seconds()
            scrape_duration_gauge.set(duration)

        _last_update_time = datetime.now(UTC)
        _last_update_success = False
        _last_error = str(e)


async def periodic_update() -> None:
    """Periodically update metrics every UPDATE_INTERVAL seconds."""
    config = get_config()
    interval = config.update_interval_seconds

    # Initial update
    update_metrics()

    while not _shutdown_event.is_set():
        try:
            await asyncio.wait_for(
                _shutdown_event.wait(),
                timeout=interval,
            )
            # If we get here, shutdown was requested
            break
        except TimeoutError:
            # Timeout means it's time to update
            update_metrics()


def _handle_shutdown_signal(sig: signal.Signals) -> None:
    """Handle shutdown signals gracefully.

    Args:
        sig: The signal that was received.
    """
    log.info("Received signal %s, initiating graceful shutdown", sig.name)
    _shutdown_event.set()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Args:
        _: FastAPI application (unused).

    Yields:
        None
    """
    config = get_config()

    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            log.error("Configuration error: %s", error)
        sys.exit(1)

    # Set exporter info
    exporter_info.info(
        {
            "version": __version__,
            "label_lang": config.label_lang.value,
            "update_interval": str(config.update_interval_minutes),
        }
    )

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_shutdown_signal, sig)

    # Start background task
    task = asyncio.create_task(periodic_update())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    log.info(
        "Started Iran League Exporter %s - updating every %d minutes",
        __version__,
        config.update_interval_minutes,
    )

    yield

    # Cleanup
    log.info("Shutting down...")
    _shutdown_event.set()

    # Cancel background tasks
    for task in background_tasks:
        task.cancel()

    # Wait for tasks to complete
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)

    log.info("Shutdown complete")


app = FastAPI(
    title="Iran League Exporter",
    description="Export football match schedules as Prometheus metrics for Iran league",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/metrics")
async def metrics_endpoint(_: str = Depends(verify_credentials)) -> Response:
    """Expose Prometheus metrics.

    Args:
        _: Username (from authentication).

    Returns:
        HTTP response with Prometheus metrics in text format.
    """
    with metric_lock:
        data = generate_latest(registry)

    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_endpoint() -> JSONResponse:
    """Health check endpoint.

    Returns:
        JSON response with health status.
    """
    is_healthy = _last_update_success or _last_update_time is None

    return JSONResponse(
        status_code=status.HTTP_200_OK
        if is_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "last_update": _last_update_time.isoformat() if _last_update_time else None,
            "last_update_success": _last_update_success,
            "last_error": _last_error,
            "version": __version__,
        },
    )


@app.get("/ready")
async def readiness_endpoint() -> JSONResponse:
    """Readiness check endpoint.

    Returns:
        JSON response with readiness status.
    """
    # Ready if we've had at least one successful update
    is_ready = _last_update_success

    return JSONResponse(
        status_code=status.HTTP_200_OK
        if is_ready
        else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "ready": is_ready,
            "last_update": _last_update_time.isoformat() if _last_update_time else None,
        },
    )


def start() -> None:
    """Start the application."""
    config = get_config()

    # Validate configuration early
    errors = config.validate()
    if errors:
        for error in errors:
            print(f"Configuration error: {error}", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        app="iranleague_exporter.main:app",
        host=config.http.host,
        port=config.http.port,
        workers=config.http.workers,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(asctime)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "use_colors": None,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": (
                        "%(levelprefix)s %(asctime)s %(client_addr)s - "
                        '"%(request_line)s" %(status_code)s'
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": config.log_level.value,
                    "propagate": False,
                },
                "uvicorn.error": {"level": config.log_level.value},
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        },
    )


if __name__ == "__main__":
    start()
