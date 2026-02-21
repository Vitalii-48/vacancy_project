# jobs\parsers\jooble.py

import requests
from jobs.models import Vacancy
from django.conf import settings

def fetch_jooble(keywords="Junior Python developer", location="Remote"):
    url = f"https://jooble.org/api/{settings.JOOBLE_API_KEY}"
    response = requests.post(url, json={"keywords": keywords, "location": location})
    response.raise_for_status()
    data = response.json()

    for job in data.get("jobs", []):
        Vacancy.objects.get_or_create(
            title=job["title"],
            company=job["company"],
            location=job.get("location", "Remote"),
            link=job["link"],
            source="Jooble"
        )
