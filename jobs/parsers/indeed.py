# jobs\parsers\indeed.py

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re


def fetch_indeed(keywords="Junior Python developer", location="remote"):
    """Скрапер вакансій Junior Python developer (Віддалена робота) з Indeed через requests + BeautifulSoup"""

    url = f"https://ua.indeed.com/jobs?q={keywords}&l={location}&sort=date"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # можна False для дебагу
        context = browser.new_context(
            locale="uk-UA",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            )
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("div.job_seen_beacon", timeout=10000)
        except Exception as e:
            print(f"❌ Не вдалося завантажити сторінку: {e}")
            browser.close()
            return []

        cards = page.query_selector_all("div.job_seen_beacon")

        if not cards:
            print("⚠️ Картки вакансій не знайдено. Indeed міг заблокувати запит.")
            return []

        # Параметри фільтрації
        cutoff_date = datetime.now() - timedelta(days=7)
        results = []

        for card in cards:
            # 1. Пошук основних тегів
            title_tag = card.query_selector("h2.jobTitle a")
            company_tag = card.query_selector("span[data-testid='company-name']")
            location_tag = card.query_selector("div[data-testid='text-location']")
            date_tag = card.query_selector("span[data-testid='myJobsStateDate']") \
                       or card.query_selector("span.date")
            snippet_tag = card.query_selector("div.job-snippet")

            if not title_tag:
                continue

            title = title_tag.inner_text().strip()
            title_low = title.lower()
            job_id = card.get_attribute("data-jk") or title_tag.get_attribute("data-jk") or ""
            link = f"https://ua.indeed.com/viewjob?jk={job_id}" if job_id else ""
            company = company_tag.inner_text().strip() if company_tag else "Невідомо"
            location_text = location_tag.inner_text().strip() if location_tag else ""
            snippet = snippet_tag.inner_text().strip() if snippet_tag else ""
            date_text = date_tag.inner_text().strip().lower() if date_tag else ""

            # 2. Фільтр по даті (не старіші за 7 днів)
            # Indeed показує: "1 day ago", "3 days ago", "today", "just posted"
            days_ago = 0
            if "just posted" in date_text or "today" in date_text or "щойно" in date_text:
                days_ago = 0
            else:
                match = re.search(r"(\d+)", date_text)
                if match:
                    days_ago = int(match.group(1))
                else:
                    continue  # Невідома дата — пропускаємо

            if days_ago > 7:
                continue

            # 3. Фільтр по рівню (Junior vs Middle/Senior)
            if "junior" not in title_low and "junior" not in snippet.lower():
                if any(lvl in title_low or lvl in snippet.lower() for lvl in ["middle", "senior", "lead"]):
                    continue

            # 4. Фільтр по стеку (Python)
            if "python" not in title_low and "python" not in snippet.lower():
                continue

            # 5. Фільтр по локації (Remote)
            remote_keywords = ["remote", "віддалено", "дистанційно"]
            if not any(kw in location_text.lower() for kw in remote_keywords):
                continue

            if not link:
                continue

            results.append({"title": title, "link": link, "company": company, "location": "Віддалено"})

    return results


if __name__ == "__main__":
    print("🚀 Пошук вакансій на Indeed...")
    jobs = fetch_indeed()

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        print("Виводимо список")
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"🏢 Компанія: {job['company']}")
            print(f"🔗 Посилання: {job['link']}")
