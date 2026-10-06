from datetime import datetime

import requests
from decouple import config

from jobs.exceptions import ParserError
from jobs.filters import MAX_AGE_DAYS, is_junior_level, is_python, is_recent


def fetch_joobl(api_key=None, keywords="Junior Python developer", location="Remote", days: int = MAX_AGE_DAYS) -> list[dict]:
    """Return a list of good vacancies from Jooble."""
    # If no key is given, take it from Django settings.
    if api_key is None:
        from django.conf import settings
        api_key = settings.JOOBLE_API_KEY

    url = f"https://ua.jooble.org/api/{api_key}"
    payload = {"keywords": keywords, "location": location}

    # Ask the API. Any problem becomes a ParserError.
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
    except (requests.RequestException, ValueError):
        # "from None" hides the original error: its text contains the API key.
        raise ParserError("Jooble: не вдалося отримати дані з API") from None

    results = []

    for job in jobs:
        # .get() does not crash if a field is missing.
        title = job.get("title", "").strip()
        snippet = job.get("snippet", "")
        link = job.get("link", "")
        updated = job.get("updated", "")

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
                "company": job.get("company") or "Невідомо",
                "location": "Віддалено",
            }
        )

    return results


if __name__ == "__main__":
    # Run this file directly to test the parser.
    print("Пошук вакансій на Jooble...")
    jobs = fetch_joobl(api_key=config("JOOBLE_API_KEY"))

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"Компанія: {job['company']}")
            print(f"Посилання: {job['link']}")