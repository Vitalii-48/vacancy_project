# jobs\parsers\dou.py

import feedparser
from urllib.parse import urlparse
from datetime import datetime, timedelta

def fetch_dou_rss():
    """Скрапер вакансій Junior Python developer (віддалена робота) з DOU.ua через feedparser"""

    # --- НАЛАШТУВАННЯ БРАУЗЕРА ---
    url = "https://jobs.dou.ua/vacancies/feeds/?search=junior%20Python%20developer&exp=0-1&remote&descr=1&category=Python"
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries:
        # 1. Пошук основних тегів
        title_all = entry['title']
        title = title_all.split('в')[0]

        company_link = entry.link
        company_name = urlparse(company_link).path.split("/")[2]  # після /companies/
        company = company_name.title()
        pub_date = entry.published

        # 2. Фільтр по даті (не старіші за 30 днів)
        cutoff_date = datetime.now() - timedelta(days=30)

        try:
            updated_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
            if updated_dt < cutoff_date:
                continue
        except (ValueError, TypeError):
            continue

        # Якщо всі перевірки пройдено — додаємо в результат
        results.append({
            "title": title,
            "company": company,
            "link": entry.link,
            "location": 'Віддалено'
        })

    return results


if __name__ == "__main__":
    print("🚀 Пошук вакансій на DOU.ua...")
    jobs = fetch_dou_rss()

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"🏢 Компанія: {job['company']}")
            print(f"🔗 Посилання: {job['link']}")