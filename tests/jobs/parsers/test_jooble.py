from datetime import datetime
from unittest.mock import Mock

import pytest
import requests

from jobs.exceptions import ParserError
from jobs.parsers import jooble
from jobs.parsers.jooble import fetch_joobl


class TestFetchJooble:
    @staticmethod
    def make_response(data: dict) -> Mock:
        """A factory for creating a fake object via appropriate requests (JSON API)."""
        response = Mock()
        response.json.return_value = data
        return response

    @staticmethod
    def make_job_item(
            title="Junior Python Developer",
            company="Geniusee",
            link="https://ua.jooble.org/jdp/-8664513883653161081",
            updated=None,
    ) -> dict:
        """A factory for generating a dict data for a single Jooble job vacancy."""
        if updated is None:
            updated = datetime.now().isoformat()
        return {
            "title": title,
            "updated": updated,
            "link": link,
            "company": company,
        }

    def test_returns_empty_list_when_jobs_has_no_vacancies(self, monkeypatch):
        response = self.make_response({"jobs": []})
        monkeypatch.setattr(jooble.requests, "post", Mock(return_value=response))
        assert fetch_joobl(api_key="test_key") == []

    def test_returns_vacancies_when_jobs_has_vacancies(self, monkeypatch):
        job = self.make_job_item()
        response = self.make_response({"jobs": [job]})

        monkeypatch.setattr(jooble.requests, "post", Mock(return_value=response))

        result = fetch_joobl(api_key="test_key")
        assert len(result) == 1
        assert result[0]["title"] == "Junior Python Developer"
        assert result[0]["company"] == "Geniusee"
        assert result[0]["link"] == "https://ua.jooble.org/jdp/-8664513883653161081"
        assert result[0]["location"] == "Віддалено"

    def test_raises_parser_error_when_network_fails(self, monkeypatch):
        def fake_requests_post_error(*_args, **_kwargs):
            raise requests.RequestException("Network error")

        monkeypatch.setattr(jooble.requests, "post", fake_requests_post_error)
        with pytest.raises(ParserError):
            fetch_joobl(api_key="test_key")

    def test_raises_parser_error_when_invalid_json(self, monkeypatch):
        response = Mock()
        response.json.side_effect = ValueError

        monkeypatch.setattr(jooble.requests, "post", Mock(return_value=response))
        with pytest.raises(ParserError):
            fetch_joobl(api_key="test_key")