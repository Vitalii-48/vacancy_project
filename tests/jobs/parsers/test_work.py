from datetime import datetime
import pytest
from selenium.common import WebDriverException

from jobs.parsers import work
from jobs.parsers.work import fetch_work
from jobs.exceptions import ParserError


class TestWorkParser:

    def make_job_html(
            self,
            title="Junior Python Developer",
            company="Miteyda",
            job_id="8541463",
            days_offset=0
    ):
        """A factory (make) function for generating a fake HTML job card."""
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
        <html>
          <body>
            <div class="job-link">
              <h2 class="my-0">
                <a href="/jobs/{job_id}/">{title}</a>
              </h2>
              <time datetime="{published_date}">Сьогодні</time>
              <p class="ellipsis">Dotmo is a frontier generative AI company...</p>
              <span class="mr-xs">
                <span class="strong-600">{company}</span>
              </span>
            </div>
          </body>
        </html>
        """

    def test_error_when_not_vacancies(self, monkeypatch):
        monkeypatch.setattr(work, "_get_page_html", lambda: "<html></html>")
        with pytest.raises(ParserError):
            fetch_work()

    def test_raises_parser_error_when_browser_fails(self, monkeypatch):
        def fake_chrome_init(*_args, **_kwargs):
            raise WebDriverException("The browser failed to load")

        monkeypatch.setattr(work.webdriver, "Chrome", fake_chrome_init)
        with pytest.raises(ParserError):
            fetch_work()

    def test_returns_vacancies(self, monkeypatch):
        html_content = self.make_job_html(
            title="Junior Python Developer",
            company="Miteyda",
            job_id="8541463"
        )

        monkeypatch.setattr(work, "_get_page_html", lambda: html_content)
        result = fetch_work()

        assert len(result) == 1
        assert result[0]["title"] == "Junior Python Developer"
        assert result[0]["company"] == "Miteyda"
        assert result[0]["link"] == "https://www.work.ua/jobs/8541463/"
        assert result[0]["location"] == "Дистанційно"