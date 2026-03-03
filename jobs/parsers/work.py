# jobs\parsers\work.py

from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def fetch_work():
    """Скрапер вакансій Junior Python developer (Дистанційно) з Work.ua через Selenium"""

    # --- НАЛАШТУВАННЯ БРАУЗЕРА ---
    url = "https://www.work.ua/jobs-remote-junior+python/"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(3)  # чекаємо виконання JS

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Параметри фільтрації
    cutoff_date = datetime.now() - timedelta(days=30)
    remote_keywords = ["дистанційно", "віддалено", "віддалена", "remote"]

    results = []

    # Знаходимо всі картки вакансій
    cards = soup.select("div.job-link")

    for card in cards:
        # 1. Пошук основних тегів
        title_tag = card.select_one("h2 a")
        time_tag = card.select_one("time")
        snippet_tag = card.select_one("p.ellipsis")
        company_tag = card.select_one("div.mt-xs span.strong-600")

        if not title_tag or not time_tag:
            continue


        title = title_tag.text.strip()
        link = "https://www.work.ua" + title_tag["href"]
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        company = company_tag.get_text(strip=True) if company_tag else "Невідомо"
        title_low = title.lower()

        # 2. Фільтр по даті (не старіші за 30 днів)
        try:
            updated_dt = datetime.strptime(time_tag["datetime"], "%Y-%m-%d %H:%M:%S")
            if updated_dt < cutoff_date:
                continue
        except (ValueError, TypeError):
            continue

        # 3. Фільтр по рівню (Junior vs Middle/Senior)
        # Якщо в тексті немає 'junior', перевіряємо, чи немає там 'middle/senior'
        if "junior" not in title_low and "junior" not in snippet:
            if any(lvl in title_low or lvl in snippet for lvl in ["middle", "senior", "lead"]):
                continue

        # 4. Фільтр по стеку (Python)
        if "python" not in title.lower() and "python" not in snippet.lower():
            continue

        # 5. Фільтр по локації (Дистанційно)
        # Шукаємо в span всередині блоку mt-xs
        location_spans = card.select("div.mt-xs span")
        is_remote = any(
            any(keyword in s.get_text().lower() for keyword in remote_keywords)
            for s in location_spans)

        if not is_remote:
            continue

        # Якщо всі перевірки пройдено — додаємо в результат
        results.append({"title": title, "link": link, "company": company, "location": 'Дистанційно'})

    return results


def save_work_to_db():
    """Запис знайдених вакансій на Robota.ua в базу даних"""
    from jobs.models import Vacancy

    works = fetch_work()
    saved = []
    for work in works:

        vacancy, created = Vacancy.objects.get_or_create(
            link=work["link"],
            defaults={
                'title': work["title"],
                'company': work["company"],
                'location': 'Дистанційно',
                'source': 'Work.ua',
                'is_sent': False
            }
        )
        if created:
            saved.append(vacancy)
    return saved


if __name__ == "__main__":
    print("🚀 Пошук вакансій на Work.ua...")
    works = fetch_work()

    if not works:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        print("Вивидимо список")
        for i, work in enumerate(works, 1):
            print(f"\n[{i}] {work['title']}")
            print(f"🏢 Компанія: {work['company']}")
            print(f"🔗 Посилання: {work['link']}")