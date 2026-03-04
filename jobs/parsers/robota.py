# jobs\parsers\robota.py

from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import dateparser

def fetch_robota():
    """Скрапер вакансій Junior Python developer (Віддалена робота) з Robota.ua через Playwright"""

    url = "https://robota.ua/ua/zapros/junior-python-developer/ukraine/params;scheduleIds=3;rubrics=1"

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto(url)  # Чекаємо завершення мережевої активності
        page.wait_for_load_state("domcontentloaded")
        # Додаткове очікування для рендерингу карток
        try:
            page.wait_for_selector("a.new-design-card", timeout=20000)

        except:
            print("❌ Картки вакансій не знайдено або заблоковано Cloudflare.")
            browser.close()
            return []

        cards = page.query_selector_all("a.new-design-card")

        # Створюємо одну вкладку для всіх описів
        job_page = context.new_page()

        # Параметри фільтрації
        cutoff_date = datetime.now() - timedelta(days=30)
        remote_keywords = ["дистанційно", "віддалено", "remote"]

        for  card in cards:
            # 1. Пошук основних тегів
            title_el = card.query_selector("h2")
            title = title_el.inner_text().strip()
            title_low = title.lower()

            link = "https://robota.ua" + card.get_attribute("href")

            company_el = card.query_selector("span.santa-mr-20")
            company = company_el.inner_text().strip() if company_el else "Невідомо"


            # 2. Фільтр по даті
            time_el = card.query_selector("div.santa-typo-secondary.santa-text-black-500")
            if time_el:
                time_text = time_el.inner_text().strip()
                parsed_date = dateparser.parse(time_text, languages=['uk'])
                if parsed_date < cutoff_date:
                    continue
            else:
                continue  # Пропускаємо вакансії без дати

            # 3. Фільтр по рівню (Junior vs Middle/Senior)
            if "junior" not in title_low and "trainee" not in title_low:
                if any(lvl in title_low for lvl in ["middle", "senior", "lead"]):
                    continue

            # 4. Фільтр по стеку (Python)
            # Витягуємо повний опис вакансії
            try:
                job_page.goto(link)
                job_page.wait_for_selector("#description-wrap", timeout=10000)
                description = job_page.inner_text("#description-wrap").strip()

                # додатково збираємо всі <p> всередині
                paragraphs = job_page.query_selector_all("#description-wrap p")
                p_texts = " ".join([p.inner_text().strip() for p in paragraphs])

                # перевірка на Python у описі
                full_text = f"{title} {description} {p_texts}".lower()
                if "python" not in full_text:
                    continue

            except Exception as e:
                print(f"⚠️ Не вдалося отримати опис: {link} ({e})")
                continue

            # 5. Фільтр по локації (Віддалена робота)
            is_remote = any(keyword in card.inner_text().lower() for keyword in remote_keywords)
            if not is_remote:
                continue

            results.append({"title": title, "link": link, "company": company, "location": 'Віддалена робота'})

        job_page.close()
        browser.close()

    return results


if __name__ == "__main__":
    print("🚀 Пошук вакансій на Robota.ua...")
    jobs = fetch_robota()

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        print("Вивидимо список")
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"🏢 Компанія: {job['company']}")
            print(f"🔗 Посилання: {job['link']}")