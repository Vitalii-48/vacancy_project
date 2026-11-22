from datetime import datetime, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest
import requests

from jobs.exceptions import ParserError
from jobs.parsers.dou import _company_from_link, _parse_date, fetch_dou_rss
from jobs.parsers import dou


class TestCompanyFromLink:
    def test_returns_company_from_link(self):
        link = "https://jobs.dou.ua/companies/miteyda/vacancies/374997/?utm_source=jobsrss"
        assert _company_from_link(link) == "Miteyda"

    def test_returns_unknown_company_from_link(self):
        link = "https://jobs.dou.ua/companies/"
        assert _company_from_link(link) == "Невідомо"


class TestParseDate:
    def test_returns_datetime_from_rss_date(self):
        assert _parse_date("Tue, 20 Oct 2026 10:30:00 +0300") == datetime(2026,10,20, 10, 30)

    def test_returns_none_from_invalid_rss_date(self):
        assert _parse_date("not a date") is None


class TestFetchDouRss:
    @staticmethod
    def make_response(text: str):
        response = Mock()
        response.content = text.encode('utf-8')
        return response

    @staticmethod
    def make_rss_item(
        title="Junior Python Developer в Miteyda, віддалено",
        link="https://jobs.dou.ua/companies/miteyda/vacancies/374997/?utm_source=jobsrss",
        published_date=None,
    ) -> str:
        if published_date is None:
            published_date = format_datetime(datetime.now(timezone.utc))
        return f"""
            <item>
                <title>{title}</title>
                <link>{link}</link>
                <pubDate>{published_date}</pubDate>
            </item>
        """

    @staticmethod
    def make_rss_feed(items_xml: str = "") -> str:
        return f"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>DOU Vacancies</title>
                <link>https://jobs.dou.ua</link>
                {items_xml}
            </channel>
        </rss>"""

    def test_returns_empty_list_when_feed_has_no_vacancies(self, monkeypatch):
        text = self.make_rss_feed()
        response = self.make_response(text)
        monkeypatch.setattr(dou.requests, "get", Mock(return_value=response))
        assert fetch_dou_rss() == []

    def test_returns_vacancies_when_feed_has_vacancies(self, monkeypatch):
        item = self.make_rss_item()
        text = self.make_rss_feed(item)
        response = self.make_response(text)

        monkeypatch.setattr(dou.requests, "get", Mock(return_value=response))

        result = fetch_dou_rss()
        assert len(result) == 1
        assert result[0]["title"] == "Junior Python Developer"
        assert result[0]["company"] == "Miteyda"
        assert result[0]["link"] == "https://jobs.dou.ua/companies/miteyda/vacancies/374997/?utm_source=jobsrss"
        assert result[0]["location"] == "Віддалено"


    def test_raises_parser_error_when_invalid_feed(self, monkeypatch):
        response = self.make_response("this is not xml")
        monkeypatch.setattr(dou.requests, "get", Mock(return_value=response))
        with pytest.raises(ParserError):
            fetch_dou_rss()


    def test_raises_parser_error_when_network_fails(self, monkeypatch):
        def fake_requests_get_error(*_args, **_kwargs):
            raise requests.RequestException("Network error")

        monkeypatch.setattr(dou.requests, "get", fake_requests_get_error)
        with pytest.raises(ParserError):
            fetch_dou_rss()