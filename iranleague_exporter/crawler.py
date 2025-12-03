"""Crawler module for fetching Iran football league match schedules."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import jdatetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from slugify import slugify
from urllib3.util.retry import Retry

from iranleague_exporter.config import CrawlerConfig, Language, get_config

if TYPE_CHECKING:
    from requests import Session

log = logging.getLogger("uvicorn.error")


class CrawlerError(Exception):
    """Custom exception for crawler errors."""

    pass


class HTTPError(CrawlerError):
    """HTTP-related errors."""

    def __init__(self, status_code: int, message: str = "") -> None:
        """Initialize HTTP error.

        Args:
            status_code: HTTP status code.
            message: Optional error message.
        """
        self.status_code = status_code
        super().__init__(message or f"HTTP error: {status_code}")


class ParseError(CrawlerError):
    """HTML parsing errors."""

    pass


def _create_session(config: CrawlerConfig) -> Session:
    """Create a requests session with retry configuration.

    Args:
        config: Crawler configuration.

    Returns:
        Session: Configured requests session.
    """
    session = requests.Session()

    # Configure retry strategy with exponential backoff
    retry_strategy = Retry(
        total=config.max_retries,
        backoff_factor=config.retry_backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update(
        {
            "User-Agent": config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )

    return session


def _parse_date_time(date_str: str, time_str: str) -> int:
    """Parse Persian date and time to Unix timestamp.

    Args:
        date_str: Persian date string in format "YYYY/MM/DD".
        time_str: Time string in format "HH:MM".

    Returns:
        int: Unix timestamp.

    Raises:
        ParseError: If date/time cannot be parsed.
    """
    try:
        date_parts = list(map(int, date_str.split("/")))
        if len(date_parts) != 3:
            raise ParseError(f"Invalid date format: {date_str}")

        gregorian_date = jdatetime.date(
            year=date_parts[0],
            month=date_parts[1],
            day=date_parts[2],
        ).togregorian()

        # Default to midnight if time is missing
        if not time_str or time_str.strip() == "":
            time_str = "00:00"

        datetime_obj = datetime.strptime(
            f"{gregorian_date} {time_str}", "%Y-%m-%d %H:%M"
        )
        return int(datetime_obj.timestamp())

    except (ValueError, IndexError) as e:
        raise ParseError(f"Failed to parse date/time: {date_str} {time_str}") from e


def _parse_match_row(row: Any, lang: Language) -> dict[str, Any] | None:
    """Parse a single match row from the HTML table.

    Args:
        row: BeautifulSoup row element.
        lang: Language for team names.

    Returns:
        dict or None: Match data dictionary or None if row should be skipped.
    """
    columns = row.find_all("td")
    if len(columns) < 7:
        return None

    home_team = columns[0].get_text(strip=True)
    away_team = columns[2].get_text(strip=True)
    score = columns[1].get_text(strip=True)

    # Skip matches that have already been played
    if score != "-":
        return None

    teams = f"{home_team} vs {away_team}"

    # Slugify team names for non-Persian languages (better for Prometheus labels)
    if lang != Language.FA:
        teams = slugify(teams, lowercase=False).replace("-vs-", " vs ")

    date_str = columns[3].get_text(strip=True)
    time_str = columns[4].get_text(strip=True)

    try:
        timestamp = _parse_date_time(date_str, time_str)
    except ParseError as e:
        log.warning("Failed to parse match date/time: %s", e)
        return None

    return {
        "teams": teams,
        "timestamp": timestamp,
    }


def get_matches(
    lang: str | Language,
    url: str | None = None,
    session: Session | None = None,
) -> list[dict[str, Any]]:
    """Crawl the match schedule website and extract future matches.

    Args:
        lang: Language for team names ("FA" or "EN", or Language enum).
        url: Optional URL override (defaults to config URL).
        session: Optional requests session (for testing).

    Returns:
        list: List of dictionaries with "teams" and "timestamp" keys.

    Raises:
        HTTPError: If HTTP request fails.
        CrawlerError: If crawling fails for other reasons.
    """
    config = get_config().crawler

    # Normalize language to enum
    if isinstance(lang, str):
        try:
            lang = Language(lang.upper())
        except ValueError:
            log.warning("Invalid language '%s', defaulting to EN", lang)
            lang = Language.EN

    # Use provided URL or default from config
    target_url = url or config.url

    # Create session if not provided
    own_session = session is None
    if session is None:
        session = _create_session(config)

    try:
        log.debug("Fetching match data from %s", target_url)

        response = session.get(
            url=target_url,
            timeout=(config.connect_timeout, config.read_timeout),
        )

        if response.status_code != 200:
            log.error("Failed to fetch data: HTTP %d", response.status_code)
            raise HTTPError(response.status_code)

        return _parse_matches_html(response.text, lang)

    except requests.exceptions.Timeout as e:
        log.error("Request timeout while fetching match data")
        raise CrawlerError("Request timeout") from e

    except requests.exceptions.ConnectionError as e:
        log.error("Connection error while fetching match data: %s", e)
        raise CrawlerError("Connection failed") from e

    except requests.exceptions.RequestException as e:
        log.error("Request failed: %s", e)
        raise CrawlerError(f"Request failed: {e}") from e

    finally:
        if own_session:
            session.close()


def _parse_matches_html(html: str, lang: Language) -> list[dict[str, Any]]:
    """Parse HTML content and extract match data.

    Args:
        html: HTML content string.
        lang: Language for team names.

    Returns:
        list: List of match dictionaries.
    """
    if not html or not html.strip():
        log.warning("Received empty HTML content")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Find all week rows
    weeks = soup.select("div.row[class='row']")
    log.debug("Found %d weeks", len(weeks))

    future_matches: list[dict[str, Any]] = []

    for week_index, week in enumerate(weeks, start=1):
        # Find week divs (first is week number, second is games table)
        divs = week.find_all("div", recursive=False)
        if len(divs) < 2:
            continue

        games_table = divs[1].find("table")
        if not games_table:
            continue

        tbody = games_table.find("tbody")
        if not tbody:
            continue

        rows = tbody.find_all("tr")
        log.debug("Found %d matches in week %d", len(rows), week_index)

        for row in rows:
            match = _parse_match_row(row, lang)
            if match:
                log.debug("Processed match: %s", match["teams"])
                future_matches.append(match)

    log.info("Found %d future matches", len(future_matches))
    return future_matches
