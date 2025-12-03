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

UPDATE_INTERVAL = int(get_env("UPDATE_INTERVAL", 30)) * 60

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
    "ir_league_matches",
    "Timestamp of IR football league matches",
    ["teams"],
    registry=registry,
)

metric_lock = threading.Lock()


def update_metrics():
    """Fetches match data and updates the Prometheus metrics."""
    log.info("Updating metrics")
    try:
        matches = get_matches(get_env("LABEL_LANG", "EN"))
        log.debug(f"Got {len(matches)} matches")
        with metric_lock:
            # Clear existing metrics
            matches_gauge.clear()
            count = 0

            # Update metrics with new data
            for match in matches:
                teams = match.get("teams")
                timestamp = match.get("timestamp")
                if all(v is not None for v in (teams, timestamp)):
                    matches_gauge.labels(teams=teams).set(timestamp)
                    count += 1
        log.debug(f"Update {count} metrics")
    except Exception as e:
        log.error(f"Error updating metrics: {e}")


async def periodic_update():
    """Periodically updates metrics every `UPDATE_INTERVAL` seconds."""
    update_metrics()  # Initial update

    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
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
    log.info("Updating metrics every `%d` minutes", UPDATE_INTERVAL // 60)
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
        port=int(get_env("HTTP_PORT", 8000)),
        workers=1,  # 1 worker is enough for this purpose
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
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
                    "level": get_env("LOG_LEVEL", "INFO"),
                    "propagate": False,
                },
                "uvicorn.error": {"level": get_env("LOG_LEVEL", "INFO")},
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
