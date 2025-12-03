"""Crawler module."""

import logging
from datetime import datetime

import jdatetime
import requests
from bs4 import BeautifulSoup
from slugify import slugify

# URL of the Persian Gulf Pro League match schedule
URL = "https://iranleague.ir/fa/MatchSchedule/1/1"

log = logging.getLogger("uvicorn.error")


def get_matches(lang: str, url: str = URL) -> list:
    """Crawl the match schedule website and extract the matches.

    Args:
        lang (str): Language of the team names.
        url (str): URL of the match schedule.

    Returns:
        list: List of matches with week number, teams, and timestamp.
    """
    response = requests.get(url=url, timeout=(5, 5))
    if response.status_code != 200:
        log.error(f"Failed to fetch data: HTTP {response.status_code}")
        return []

    # Parse the HTML content
    response = BeautifulSoup(response.text, "html.parser")

    # Find all the rows for weeks
    weeks = response.select("div.row[class='row']")
    log.debug(f"Found {len(weeks)} weeks")

    future_matches = []

    for index, week in enumerate(weeks):
        # Find the week number (first div) and games table (second div)
        divs = week.find_all("div", recursive=False)
        if len(divs) < 2:
            continue  # Skip if structure is unexpected

        games_table = divs[1].find("table")  # Locate the table

        if not games_table:
            continue  # Skip if no table is found

        # Iterate through all table rows in tbody
        rows = games_table.find("tbody").find_all("tr")
        log.debug(f"Found {len(rows)} matches in week {index + 1}")

        for row in rows:
            columns = row.find_all("td")
            if len(columns) < 7:
                continue  # Skip rows with unexpected structure

            teams = f"{columns[0].get_text(strip=True)} vs {columns[2].get_text(strip=True)}"  # noqa: E501
            log.debug(f"Processing match: {teams}")

            # Slugify the team names (for Prometheus labels) for non-fa lang
            if lang != "FA":
                teams = slugify(teams, lowercase=False).replace("-vs-", " vs ")

            score = columns[1].get_text(strip=True)

            date = list(map(int, columns[3].get_text(strip=True).split("/")))
            date = jdatetime.date(
                day=int(date[2]), month=date[1], year=date[0]
            ).togregorian()
            time = columns[4].get_text(strip=True)
            # If time is missing, default to "00:00".
            if not time:
                time = "00:00"
            time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            time = int(time.timestamp())

            # Check if score is '-' (no score - we need future matches)
            if score == "-":
                future_matches.append(
                    {
                        "teams": teams,
                        "timestamp": time,
                    }
                )

    return future_matches
