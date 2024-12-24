"""Main module for the Iran League exporter."""

import asyncio
import logging
import secrets
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)
from starlette.responses import Response

from iranleague_exporter.crawler import get_matches
from iranleague_exporter.utils import get_env

UPDATE_INTERVAL_SECONDS = 30 * 60

background_tasks = set()
security = HTTPBasic()
log = logging.getLogger("uvicorn.error")


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Verify the provided basic-auth credential.

    Args:
        credentials (HTTPBasicCredentials, optional): Provided credential.

    Raises:
        HTTPException: Incorrect credential.

    Returns:
        str: Username
    """
    correct_username = secrets.compare_digest(
        credentials.username,
        get_env("AUTH_USERNAME"),
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        get_env("AUTH_PASSWORD"),
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


registry = CollectorRegistry()

matches_gauge = Gauge(
    "matches_timestamp",
    "Timestamp of matches",
    ["teams"],
    registry=registry,
)

metric_lock = threading.Lock()


def update_metrics():
    """Fetches match data and updates the Prometheus metrics."""
    try:
        matches = get_matches()
        with metric_lock:
            # Clear existing metrics
            matches_gauge.clear()

            # Update metrics with new data
            for match in matches:
                week = match.get("week")
                teams = match.get("teams")
                timestamp = match.get("timestamp")
                if all(v is not None for v in (week, teams, timestamp)):
                    matches_gauge.labels(teams=teams).set(timestamp)
    except Exception as e:
        log.error(f"Error updating metrics: {e}")


async def periodic_update():
    """Periodically updates metrics every UPDATE_INTERVAL_SECONDS."""
    update_metrics()  # Initial update

    while True:
        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        update_metrics()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan function.

    Args:
        _ (FastAPI): FastAPI application.
    """
    task = asyncio.create_task(periodic_update())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/metrics")
async def metrics_endpoint(_: str = Depends(verify_credentials)) -> Response:
    """Exposes Prometheus metrics.

    Args:
        _ (str, optional): Username. Defaults to Depends(verify_credentials).

    Returns:
        Response: HTTP response with Prometheus metrics.
    """
    with metric_lock:
        data = generate_latest(registry)

    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def start():
    """Start the application."""
    uvicorn.run(
        app="iranleague_exporter.main:app",
        host=get_env("HTTP_HOST", "0.0.0.0"),
        port=get_env("HTTP_PORT", 8000),
        workers=1,  # 1 worker is enough for this purpose
    )
