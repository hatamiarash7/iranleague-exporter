# Iran Football League Exporter

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub release](https://img.shields.io/github/release/hatamiarash7/iranleague-exporter.svg)](https://GitHub.com/hatamiarash7/iranleague-exporter/releases/) [![Release](https://github.com/hatamiarash7/iranleague-exporter/actions/workflows/release.yml/badge.svg)](https://github.com/hatamiarash7/iranleague-exporter/actions/workflows/release.yml) ![GitHub](https://img.shields.io/github/license/hatamiarash7/iranleague-exporter)

Export football match schedules as Prometheus metrics for Iran league. This script will use the [https://iranleague.ir](https://iranleague.ir) site to fetch the match schedules and export them as Prometheus metrics.

## Features

- Automatic retry with exponential backoff for failed requests
- Prometheus metrics for match schedules with basic authentication
- Health check and readiness endpoints (`/health`, `/ready`)

## How-To

You can run this exporter as a Docker container:

```bash
docker run -d -p 8000:8000 \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=1234 \
  hatamiarash7/iranleague-exporter:latest
```

Check the metrics at `http://localhost:8000/metrics`.

### Endpoints

| Endpoint   | Auth Required | Description                       |
| ---------- | ------------- | --------------------------------- |
| `/metrics` | Yes           | Prometheus metrics                |
| `/health`  | No            | Health check (liveness probe)     |
| `/ready`   | No            | Readiness check (readiness probe) |

## Configuration

You can configure the exporter using the following environment variables:

### Server Configuration

| Key          | Default | Description                                       |
| ------------ | ------- | ------------------------------------------------- |
| HTTP_HOST    | 0.0.0.0 | Host to bind the HTTP server to                   |
| HTTP_PORT    | 8000    | Port to bind the HTTP server to                   |
| HTTP_WORKERS | 1       | Number of worker processes                        |
| LOG_LEVEL    | INFO    | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Authentication

| Key           | Default | Description                       |
| ------------- | ------- | --------------------------------- |
| AUTH_USERNAME |         | Username for basic authentication |
| AUTH_PASSWORD |         | Password for basic authentication |

### Crawler Configuration

| Key                     | Default                                      | Description                       |
| ----------------------- | -------------------------------------------- | --------------------------------- |
| CRAWLER_URL             | <https://iranleague.ir/fa/MatchSchedule/1/1> | URL to fetch match schedules from |
| CRAWLER_CONNECT_TIMEOUT | 5.0                                          | Connection timeout in seconds     |
| CRAWLER_READ_TIMEOUT    | 10.0                                         | Read timeout in seconds           |
| CRAWLER_MAX_RETRIES     | 3                                            | Maximum number of retry attempts  |
| CRAWLER_RETRY_BACKOFF   | 0.5                                          | Backoff factor for retries        |
| CRAWLER_USER_AGENT      | IranLeagueExporter/1.0                       | User-Agent header for requests    |

### Other Settings

| Key             | Default | Description                                         |
| --------------- | ------- | --------------------------------------------------- |
| LABEL_LANG      | EN      | Language for the team names (FA, EN)                |
| UPDATE_INTERVAL | 30      | Interval to update the match schedules (in minutes) |
| TZ              |         | Timezone (e.g., Asia/Tehran)                        |

## Prometheus Metrics

The exporter provides the following metrics:

| Metric                              | Type  | Description                             |
| ----------------------------------- | ----- | --------------------------------------- |
| `ir_league_matches`                 | Gauge | Timestamp of upcoming matches           |
| `ir_league_matches_total`           | Gauge | Total number of future matches found    |
| `ir_league_scrape_duration_seconds` | Gauge | Duration of the last scrape in seconds  |
| `ir_league_scrape_success`          | Gauge | Whether the last scrape was successful  |
| `ir_league_exporter_info`           | Info  | Exporter version and configuration info |

## Development

### Prerequisites

- Python 3.10+
- Poetry

### Setup

```bash
# Install dependencies
make install

# Run locally
make run

# Run tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Type check
make typecheck
```

---

## Support 💛

[![Donate with Bitcoin](https://img.shields.io/badge/Bitcoin-bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz-orange)](https://donatebadges.ir/donate/Bitcoin/bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz) [![Donate with Ethereum](https://img.shields.io/badge/Ethereum-0x0831bD72Ea8904B38Be9D6185Da2f930d6078094-blueviolet)](https://donatebadges.ir/donate/Ethereum/0x0831bD72Ea8904B38Be9D6185Da2f930d6078094)

<div><a href="https://payping.ir/@hatamiarash7"><img src="https://cdn.payping.ir/statics/Payping-logo/Trust/blue.svg" height="128" width="128"></a></div>

## Contributing 🤝

Don't be shy and reach out to us if you want to contribute 😉

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## Issues

Each project may have many problems. Contributing to the better development of this project by reporting them. 👍
