# Iran Football League Exporter

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub release](https://img.shields.io/github/release/hatamiarash7/iranleague-exporter.svg)](https://GitHub.com/hatamiarash7/iranleague-exporter/releases/) [![Release](https://github.com/hatamiarash7/iranleague-exporter/actions/workflows/release.yml/badge.svg)](https://github.com/hatamiarash7/iranleague-exporter/actions/workflows/release.yml) ![GitHub](https://img.shields.io/github/license/hatamiarash7/iranleague-exporter)

Export football match schedules as Prometheus metrics for Iran league. This script will use the [https://iranleague.ir](https://iranleague.ir) site to fetch the match schedules and export them as Prometheus metrics.

## How-To

You can run this exporter as a Docker container:

```bash
docker run -d -p 8000:8000 -e AUTH_USERNAME=admin -e AUTH_PASSWORD=1234 hatamiarash7/iranleague-exporter:v1.0.1
```

Check the metrics at `http://localhost:8000/metrics`.

## Configuration

You can configure the exporter using the following environment variables:

| Key             | Default | Description                                         |
| --------------- | ------- | --------------------------------------------------- |
| HTTP_HOST       | 0.0.0.0 | Host to bind the HTTP server to                     |
| HTTP_PORT       | 8000    | Port to bind the HTTP server to                     |
| LOG_LEVEL       | INFO    | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)   |
| AUTH_USERNAME   |         | Username for basic authentication                   |
| AUTH_PASSWORD   |         | Password for basic authentication                   |
| LABEL_LANG      | FA      | Language for the team names (FA, EN)                |
| UPDATE_INTERVAL | 30      | Interval to update the match schedules (in minutes) |

Also, you can use the `TZ` environment variable to set the timezone for the exporter. The default timezone is dependent on the host system. Set it to `Asia/Tehran` to get the Iran timezone.

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
