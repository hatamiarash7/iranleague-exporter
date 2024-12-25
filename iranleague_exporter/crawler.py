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


def get_matches(url: str = URL) -> list:
    """Crawl the match schedule website and extract the matches.

    Args:
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

    future_matches = []

    for week in weeks:
        # Find the week number (first div) and games table (second div)
        divs = week.find_all("div", recursive=False)
        if len(divs) < 2:
            continue  # Skip if structure is unexpected

        # week_number = divs[0].get_text(strip=True)  # Extract the week number
        games_table = divs[1].find("table")  # Locate the table

        if not games_table:
            continue  # Skip if no table is found

        # Iterate through all table rows in tbody
        rows = games_table.find("tbody").find_all("tr")
        for row in rows:
            columns = row.find_all("td")
            if len(columns) < 7:
                continue  # Skip rows with unexpected structure

            team_a = columns[0].get_text(strip=True)
            team_b = columns[2].get_text(strip=True)

            score = columns[1].get_text(strip=True)

            date = list(map(int, columns[3].get_text(strip=True).split("/")))
            date = jdatetime.date(
                day=int(date[2]), month=date[1], year=date[0]
            ).togregorian()
            time = columns[4].get_text(strip=True)
            time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            time = int(time.timestamp())

            # Check if score is '-' (no score - we need future matches)
            if score == "-":
                future_matches.append(
                    {
                        # "week": week_number[5:],
                        "teams": slugify(f"{team_a} vs {team_b}", lowercase=False),
                        "timestamp": time,
                    }
                )

    return future_matches
