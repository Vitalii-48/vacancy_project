# jobs\parsers\jooble.py

import requests
from decouple import config
from datetime import datetime, timedelta


def fetch_joobl(api_key=None, keywords="Junior Python developer", location="Remote"):
    """Скрапер вакансій Junior Python developer (за замовчуванням) (Дистанційно) з API Jooble."""

    if api_key is None:
        from django.conf import settings
        api_key = settings.JOOBLE_API_KEY
    url = f"https://ua.jooble.org/api/{api_key}"
    payload = {"keywords": keywords, "location": location}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        jobs = data.get('jobs', [])
        results = []

        # Параметри фільтрації
        cutoff_date = datetime.now() - timedelta(days=7)

        for job in jobs:
            # 1. Пошук основних тегів
            title = job["title"].lower()
            snippet = job["snippet"].lower()
            company = job["company"]
            link = job["link"]
            updated_str = job["updated"].split("T")[0]


            # 2. Фільтр по даті (не старіші за 7 днів)
            try:
                updated_dt = datetime.fromisoformat(updated_str)

                if updated_dt < cutoff_date:
                    continue

            except ValueError:
                continue


            # 3. Фільтр по рівню (Junior vs Middle/Senior)
            if "junior" not in title and "junior" not in snippet:
                if "middle" in title or "senior" in title or "middle" in snippet or "senior" in snippet:
                    continue

            # 4. Фільтр по стеку (Python)
            if "python" not in title and "python" not in snippet:
                continue

            results.append({"title": title, "link": link, "company": company, "location": 'Віддалено'})

        return results

    except Exception as e:
        print(f"❌ Помилка: {e}")
        return []




if __name__ == "__main__":
    api_key_jooble = config("JOOBLE_API_KEY")
    print("🚀 Пошук вакансій на Jooble...")
    jobs = fetch_joobl(api_key=api_key_jooble)

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        print("Вивидимо список")
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"🏢 Компанія: {job['company']}")
            print(f"🔗 Посилання: {job['link']}")
