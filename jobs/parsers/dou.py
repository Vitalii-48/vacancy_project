import html
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import requests

from jobs.constants import DEFAULT_DAYS, USER_AGENT
from jobs.exceptions import ParserError
from jobs.filters import is_junior_level, is_recent

# The site already filters: experience 1-3 years, remote, Python.
URL = f"https://jobs.dou.ua/vacancies/feeds/?exp=1-3&remote&category=Python"# DOU blocks the default "python-requests" name, so we look like a browser.
HEADERS = {"User-Agent": USER_AGENT}
NETWORK_TIMEOUT = 15

# Marker constants and RSS-keys
RSS_TITLE_KEY = "title"
RSS_LINK_KEY = "link"
RSS_PUBLISHED_KEY = "published"

COMPANY_SPLIT_MARKER = " в "


def _company_from_link(link: str) -> str:
    """Take the company name from the link: /companies/<name>/vacancies/..."""
    parts = urlparse(link).path.split("/")
    return parts[2].title() if len(parts) > 2 and parts[2] else "Невідомо"


def _parse_date(value: str) -> datetime | None:
    """Turn the RSS date text into a datetime. Return None if it is broken."""
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def fetch_dou_rss(days: int = DEFAULT_DAYS) -> list[dict]:
    """Return a list of good vacancies from DOU.ua."""
    # Download the feed. Any network problem becomes a ParserError.
    try:
        response = requests.get(URL, headers=HEADERS, timeout=NETWORK_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ParserError("DOU: не вдалося отримати RSS") from e

    feed = feedparser.parse(response.content)
    # "bozo" check: ensure the stream is neither corrupted nor empty
    if feed.bozo and not feed.entries:
        raise ParserError("DOU: RSS не вдалося розібрати")

    results = []

    for entry in feed.entries:
        # The title looks like "Job name в Company": cut only the end part.
        title = html.unescape(entry.get(RSS_TITLE_KEY, "").rsplit(COMPANY_SPLIT_MARKER, 1)[0]).strip()
        link = entry.get(RSS_LINK_KEY, "")
        if not title or not link:
            continue  # skip broken entries

        # Skip vacancies with a broken or old date.
        published = _parse_date(entry.get(RSS_PUBLISHED_KEY, ""))
        if published is None or not is_recent(published,days):
            continue

        # Skip senior vacancies (we check only the title here).
        if not is_junior_level(str(title)):
            continue

        results.append(
            {
                "title": title,
                "company": _company_from_link(link),
                "link": link,
                "location": "Віддалено",
            }
        )

    return results


if __name__ == "__main__":
    # Run this file directly to test the parser.
    print("Пошук вакансій на DOU.ua...")
    jobs = fetch_dou_rss()

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"Компанія: {job['company']}")
            print(f"Посилання: {job['link']}")