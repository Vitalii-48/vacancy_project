from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from jobs.exceptions import ParserError
from jobs.filters import MAX_AGE_DAYS, is_junior_level, is_recent

# The address already filters: remote jobs, Python.
URL = "https://www.work.ua/jobs-remote-python/"
# Pretend to be a normal browser.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)


def _get_page_html() -> str:
    """Open the page in a browser and return its HTML."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # run without a window
    options.add_argument(f"user-agent={USER_AGENT}")

    try:
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(URL)
            # Wait up to 10 seconds until vacancy cards appear.
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements("css selector", "div.job-link")
            )
            return driver.page_source
        finally:
            driver.quit()  # always close the browser, even after an error
    except WebDriverException as e:
        raise ParserError(
            "Work.ua: не вдалося отримати сторінку (браузер або верстка)"
        ) from e


def fetch_work(days: int = MAX_AGE_DAYS) -> list[dict]:
    """Return a list of good vacancies from Work.ua."""
    soup = BeautifulSoup(_get_page_html(), "html.parser")

    # Each vacancy is one "card" on the page.
    cards = soup.select("div.job-link")
    if not cards:
        raise ParserError("Work.ua: картки не знайдено (змінилась верстка?)")

    results = []

    for card in cards:
        # Find the parts of the card.
        title_tag = card.select_one("h2 a")
        time_tag = card.select_one("time")
        snippet_tag = card.select_one("p.ellipsis")
        company_tag = card.select_one("span.mr-xs span.strong-600")

        if not title_tag or not time_tag:
            continue  # not a real vacancy card

        title = title_tag.get_text(strip=True)
        link = "https://www.work.ua" + str(title_tag["href"])
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        company = company_tag.get_text(strip=True) if company_tag else "Невідомо"

        # Read the publish date. Skip the card if the date is broken.
        try:
            published = datetime.strptime(
                str(time_tag["datetime"]), "%Y-%m-%d %H:%M:%S"
            )
        except (ValueError, TypeError):
            continue

        if not is_recent(published, days):
            continue
        if not is_junior_level(title, snippet):
            continue

        results.append(
            {
                "title": title,
                "link": link,
                "company": company,
                "location": "Дистанційно",
            }
        )

    return results


if __name__ == "__main__":
    # Run this file directly to test the parser.
    print("Пошук вакансій на Work.ua...")
    works = fetch_work()

    if not works:
        print("Нічого не знайдено за вашими критеріями.")
    else:
        for i, work in enumerate(works, 1):
            print(f"\n[{i}] {work['title']}")
            print(f"Компанія: {work['company']}")
            print(f"Посилання: {work['link']}")