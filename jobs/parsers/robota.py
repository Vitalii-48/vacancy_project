import dateparser
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Locator, Page
from playwright_stealth import Stealth
from urllib.parse import urljoin

from jobs.constants import USER_AGENT
from jobs.exceptions import ParserError
from jobs.filters import is_junior_level, is_recent

ROBOTA_BASE_URL = "https://robota.ua"
# The address already filters: remote jobs, IT category.
URL = f"{ROBOTA_BASE_URL}/zapros/python/ukraine/params;scheduleIds=3;rubrics=1"

# CSS selectors: the site can change them, so they all live here.
VACANCY_CARD_SELECTOR = "a.new-design-card"
TITLE_SELECTOR = "h2"
COMPANY_SELECTOR = "span.santa-mr-20"
DATE_SELECTOR = "div.santa-typo-secondary.santa-text-black-500"
DESCRIPTION_SELECTOR = "#description-wrap"

REMOTE_KEYWORDS = ["дистанційно", "віддалено", "remote"]


def _open_vacancy_list(browser: Browser) -> tuple[BrowserContext, Page]:
    """Open the vacancies page and wait until the cards appear."""
    context = browser.new_context(user_agent=USER_AGENT)
    page = context.new_page()


    # Wait for vacancy cards. If they never appear, Cloudflare blocked us.
    try:
        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_selector(VACANCY_CARD_SELECTOR, timeout=20000)
    except Exception as e:
        context.close()
        raise ParserError(
            "Robota: картки не знайдено (ймовірно, Cloudflare)"
        ) from e
    return context, page


def _text(card: Locator, selector: str) -> str:
    """Text of the first element that matches the selector, or "" if there is none."""
    found = card.locator(selector)
    if found.count() == 0:  # count() does not wait: it answers at once
        return ""
    return found.first.inner_text().strip()


def fetch_robota() -> list[dict]:
    """Return a list of good vacancies from Robota.ua."""
    results = []

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        try:  # "finally" below always closes the browser
            context, page = _open_vacancy_list(browser)

            # One extra tab is used to open every vacancy page.
            job_page = context.new_page()

            for card in page.locator(VACANCY_CARD_SELECTOR).all():
                title = _text(card, TITLE_SELECTOR)
                if not title:
                    continue  # not a real vacancy card

                href = card.get_attribute("href")
                if not href:
                    continue

                link = urljoin(ROBOTA_BASE_URL, href or "")

                company = _text(card, COMPANY_SELECTOR) or "Невідомо"

                # Read the date. Skip the card if there is no date.
                date_text = _text(card, DATE_SELECTOR)
                if not date_text:
                    continue
                published = dateparser.parse(date_text, languages=["uk"])
                if published is None:  # dateparser did not understand the text
                    continue
                if not is_recent(published):
                    continue

                if not is_junior_level(title):
                    continue

                # Open the vacancy page and look for "python" in the full text.
                try:
                    job_page.goto(link)
                    job_page.wait_for_selector(DESCRIPTION_SELECTOR, timeout=10000)
                    description = job_page.inner_text(DESCRIPTION_SELECTOR).strip()
                except Exception as e:
                    print(f" Не вдалося отримати опис: {link} ({e})")
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