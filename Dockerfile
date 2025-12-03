FROM --platform=$BUILDPLATFORM python:3.14-slim AS builder

ARG APP_VERSION="undefined@docker"
ARG DATE_CREATED

ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONFAULTHANDLER=true \
    PYTHONUNBUFFERED=true \
    PYTHONHASHSEED=random \
    PYTHONPATH=/usr/lib/python3/dist-packages \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry
    POETRY_NO_INTERACTION=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VERSION=1.8.5 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/poetry' \
    POETRY_HOME='/opt/poetry'

LABEL org.opencontainers.image.title="iranleague-exporter"
LABEL org.opencontainers.image.description="Export football match schedules as Prometheus metrics for Iran league."
LABEL org.opencontainers.image.url="https://github.com/hatamiarash7/iranleague-exporter"
LABEL org.opencontainers.image.source="https://github.com/hatamiarash7/iranleague-exporter"
LABEL org.opencontainers.image.vendor="hatamiarash7"
LABEL org.opencontainers.image.author="hatamiarash7"
LABEL org.opencontainers.version="$APP_VERSION"
LABEL org.opencontainers.image.created="$DATE_CREATED"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 - && sleep 5

ENV PATH="/opt/poetry/bin:$PATH"

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN poetry install --without dev,test --no-interaction --no-ansi

COPY . .

CMD ["python", "-m", "iranleague_exporter"]
