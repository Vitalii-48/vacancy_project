# NOTE: disabled now, Cloudflare blocks this parser.

import dateparser
from playwright.sync_api import sync_playwright

from jobs.exceptions import ParserError
from jobs.filters import is_junior_level, is_recent

# The address already filters: remote jobs, IT category.
URL = "https://robota.ua/ua/zapros/junior-python-developer/ukraine/params;scheduleIds=3;rubrics=1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)
REMOTE_KEYWORDS = ["дистанційно", "віддалено", "remote"]


def fetch_robota() -> list[dict]:
    """Return a list of good vacancies from Robota.ua."""
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:  # "finally" below always closes the browser
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            page.goto(URL)

            # Wait for vacancy cards. If they never appear, Cloudflare blocked us.
            try:
                page.wait_for_selector("a.new-design-card", timeout=20000)
            except Exception as e:
                raise ParserError(
                    "Robota: картки не знайдено (ймовірно, Cloudflare)"
                ) from e

            cards = page.query_selector_all("a.new-design-card")
            # One extra tab is used to open every vacancy page.
            job_page = context.new_page()

            for card in cards:
                title_el = card.query_selector("h2")
                if not title_el:
                    continue  # not a real vacancy card
                title = title_el.inner_text().strip()
                link = "https://robota.ua" + (card.get_attribute("href") or "")

                company_el = card.query_selector("span.santa-mr-20")
                company = company_el.inner_text().strip() if company_el else "Невідомо"

                # Read the date. Skip the card if there is no date.
                time_el = card.query_selector("div.santa-typo-secondary.santa-text-black-500")
                if not time_el:
                    continue
                published = dateparser.parse(time_el.inner_text().strip(), languages=["uk"])
                if published is None:  # dateparser did not understand the text
                    continue
                if not is_recent(published):
                    continue

                if not is_junior_level(title):
                    continue

                # Open the vacancy page and look for "python" in the full text.
                try:
                    job_page.goto(link)
                    job_page.wait_for_selector("#description-wrap", timeout=10000)
                    description = job_page.inner_text("#description-wrap").strip()
                except Exception as e:
                    print(f"⚠️ Не вдалося отримати опис: {link} ({e})")
                    continue
                if "python" not in f"{title} {description}".lower():
                    continue

                # Check that the card says it is remote work.
                card_text = card.inner_text().lower()
                if not any(word in card_text for word in REMOTE_KEYWORDS):
                    continue

                results.append(
                    {
                        "title": title,
                        "link": link,
                        "company": company,
                        "location": "Віддалена робота",
                    }
                )
        finally:
            browser.close()

    return results


if __name__ == "__main__":
    # Run this file directly to test the parser.
    print("Пошук вакансій на Robota.ua...")
    jobs = fetch_robota()

    if not jobs:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}] {job['title']}")
            print(f"Компанія: {job['company']}")
            print(f"Посилання: {job['link']}")