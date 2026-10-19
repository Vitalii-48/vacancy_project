from datetime import datetime

import requests
from decouple import config

from jobs.constants import DEFAULT_DAYS
from jobs.exceptions import ParserError
from jobs.filters import is_junior_level, is_python, is_recent

# Configuration constants and API
JOOBLE_BASE_URL = "https://ua.jooble.org/api"
NETWORK_TIMEOUT = 15

# Default search settings
JOOBLE_KEYWORDS = "Python"
JOOBLE_LOCATION = "Remote"

# Jooble API JSON response keys
API_JOBS_KEY = "jobs"
API_TITLE_KEY = "title"
API_SNIPPET_KEY = "snippet"
API_LINK_KEY = "link"
API_UPDATED_KEY = "updated"
API_COMPANY_KEY = "company"


def fetch_joobl(
        api_key=None,
        keywords=JOOBLE_KEYWORDS,
        location=JOOBLE_LOCATION,
        days: int = DEFAULT_DAYS,
) -> list[dict]:
    """Return a list of good vacancies from Jooble."""
    # If no key is given, take it from Django settings.
    if api_key is None:
        from django.conf import settings
        api_key = settings.JOOBLE_API_KEY

    url = f"{JOOBLE_BASE_URL}/{api_key}"
    payload = {"keywords": keywords, "location": location}

    # Ask the API. Any problem becomes a ParserError.
    try:
        response = requests.post(url, json=payload, timeout=NETWORK_TIMEOUT)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
    except (requests.RequestException, ValueError):
        # "from None" hides the original error: its text contains the API key.
        raise ParserError("Jooble: не вдалося отримати дані з API") from None

    results = []

    for job in jobs:
        # .get() does not crash if a field is missing.
        title = job.get(API_TITLE_KEY, "").strip()
        snippet = job.get(API_SNIPPET_KEY, "")
        link = job.get(API_LINK_KEY, "")
        updated = job.get(API_UPDATED_KEY, "")

        if not title or not link:
            continue  # skip broken records

        # Take only the date part (before the "T").
        try:
            published = datetime.fromisoformat(updated.split("T")[0])
        except ValueError:
            continue

        if not is_recent(published, days):
            continue
        if not is_junior_level(title, snippet):
            continue
        # Jooble search is not exact, so we check for Python ourselves.
        if not is_python(title, snippet):
            continue

        results.append(
            {
                "title": title,
                "link": link,
                "company": job.get(API_COMPANY_KEY) or "Невідомо",
                "location": "Віддалено",
            }
        )

    return results


if __name__ == "__main__":
    # Run this file directly to test the parser.
    print("Пошук вакансій на Jooble...")
    jobs_prt = fetch_joobl(api_key=config("JOOBLE_API_KEY"))

    if not jobs_prt:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, job_prt in enumerate(jobs_prt, 1):
            print(f"\n[{i}] {job_prt['title']}")
            print(f"Компанія: {job_prt['company']}")
            print(f"Посилання: {job_prt['link']}")