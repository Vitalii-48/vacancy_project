import html
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import requests

from jobs.exceptions import ParserError
from jobs.filters import MAX_AGE_DAYS, is_junior_level, is_recent

# The site already filters: experience 1-3 years, remote, Python.
URL = "https://jobs.dou.ua/vacancies/feeds/?exp=1-3&remote&category=Python"
# DOU blocks the default "python-requests" name, so we look like a browser.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
}


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


def fetch_dou_rss(days: int = MAX_AGE_DAYS) -> list[dict]:
    """Return a list of good vacancies from DOU.ua."""
    # Download the feed. Any network problem becomes a ParserError.
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ParserError("DOU: не вдалося отримати RSS") from e

    feed = feedparser.parse(response.content)
    # "bozo" means the feed is broken. Empty and broken is a real failure.
    if feed.bozo and not feed.entries:
        raise ParserError("DOU: RSS не вдалося розібрати")

    results = []

    for entry in feed.entries:
        # The title looks like "Job name в Company": cut only the end part.
        title = html.unescape(entry.get("title", "").rsplit(" в ", 1)[0]).strip()
        link = entry.get("link", "")
        if not title or not link:
            continue  # skip broken entries

        # Skip vacancies with a broken or old date.
        published = _parse_date(entry.get("published", ""))
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