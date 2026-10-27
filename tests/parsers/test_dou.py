from datetime import datetime, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest
import requests

from jobs.exceptions import ParserError


from jobs.parsers.dou import _company_from_link, _parse_date, fetch_dou_rss
from jobs.parsers import dou

published = format_datetime(datetime.now(timezone.utc))

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
    def make_response(self, text: str):
        response = Mock()
        response.content = text.encode('utf-8')
        return response

    def test_returns_empty_list_when_feed_has_no_vacancies(self, monkeypatch):
        text = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
        response = self.make_response(text)
        monkeypatch.setattr(dou.requests, "get", Mock(return_value=response))
        assert fetch_dou_rss() == []

    def fake_requests_get_with_vacancy(self, *_args, **_kwargs):
        text = f"""<rss version="2.0"><channel> <item>
                <title>Junior Python Developer в Miteyda, віддалено</title>
                <link>https://jobs.dou.ua/companies/miteyda/vacancies/374997/?utm_source=jobsrss</link>
                <pubDate>{published}</pubDate>
                </item></channel></rss>"""
        return self.make_response(text)

    def test_returns_vacancies_when_feed_has_vacancies(self, monkeypatch):
        monkeypatch.setattr(dou.requests, "get", self.fake_requests_get_with_vacancy)
        result = fetch_dou_rss()
        assert len(result) == 1
        assert result[0]["title"] == "Junior Python Developer"
        assert result[0]["company"] == "Miteyda"
        assert result[0]["link"] == "https://jobs.dou.ua/companies/miteyda/vacancies/374997/?utm_source=jobsrss"
        assert result[0]["location"] == "Віддалено"

    def fake_requests_get_error_for_feed(self, *_args, **_kwargs):
        text = 'this is not xml'
        return self.make_response(text)

    def test_raises_parser_error_when_invalid_feed(self, monkeypatch):
        monkeypatch.setattr(dou.requests, "get", self.fake_requests_get_error_for_feed)
        with pytest.raises(ParserError):
            fetch_dou_rss()

    def fake_requests_get_error(self, *args, **kwargs):
        raise requests.RequestException("Network error")

    def test_raises_parser_error_when_network_fails(self, monkeypatch):
        monkeypatch.setattr(dou.requests, "get", self.fake_requests_get_error)
        with pytest.raises(ParserError):
            fetch_dou_rss()