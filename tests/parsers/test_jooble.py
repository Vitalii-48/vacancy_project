from datetime import datetime
from jobs.exceptions import ParserError
from unittest.mock import Mock

import pytest
import requests

from jobs.parsers import jooble
from jobs.parsers.jooble import fetch_joobl


published = datetime.now().isoformat()

def fake_response(data):
    response = Mock()
    response.json.return_value = data
    return response

def test_returns_empty_list_when_jobs_has_no_vacancies(monkeypatch):
    data = {"jobs": []}
    monkeypatch.setattr(jooble.requests, "post", Mock(return_value=fake_response(data)))
    assert fetch_joobl(api_key="test_key") ==[]

def test_returns_vacancies_when_jobs_has_vacancies(monkeypatch):
    data = {
        "jobs": [
            {
                "title": "Junior Python Developer",
                "updated": published,
                "link": "https://ua.jooble.org/jdp/-8664513883653161081",
                "company": "Geniusee",
            }
        ]
    }
    monkeypatch.setattr(jooble.requests, "post", Mock(return_value=fake_response(data)))
    result = fetch_joobl(api_key="test_key")
    assert len(result) == 1
    assert result[0]["title"] == "Junior Python Developer"
    assert result[0]["company"] == "Geniusee"
    assert result[0]["link"] == "https://ua.jooble.org/jdp/-8664513883653161081"
    assert result[0]["location"] == "Віддалено"



def test_raises_parser_error_when_network_fails(monkeypatch):
    def fake_requests_post_error(*_args, **_kwargs):
        raise requests.RequestException("Network error")

    monkeypatch.setattr(jooble.requests, "post", fake_requests_post_error)
    with pytest.raises(ParserError):
        fetch_joobl(api_key="test_key")

def test_raises_parser_error_when_invalid_json(monkeypatch):
    response = Mock()
    response.json.side_effect = ValueError

    monkeypatch.setattr(jooble.requests, "post", Mock(return_value=response))
    with pytest.raises(ParserError):
        fetch_joobl(api_key="test_key")