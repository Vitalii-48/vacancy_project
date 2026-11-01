from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model

from jobs import services
from jobs.constants import DEFAULT_DAYS
from jobs.exceptions import ParseNotAllowed, ParserError
from jobs.models import Vacancy, UserVacancy, ParseRun
from jobs.services import (
    ingest_vacancies,
    set_vacancy_status,
    start_parse,
    _execute_run,
    start_parse_all
)



User = get_user_model()

DOU = Vacancy.Source.DOU.value

# Names of the actions that set_vacancy_status accepts.
APPLIED = "applied"
IRRELEVANT = "irrelevant"
RESET = "reset"

# Two vacancies, as a parser would return them.
PARSED_ITEMS = [
    {
    "title": "Junior Python Developer",
    "company": "Middels",
    "link": "https://jobs.middels.edu/",
    "location": "Віддалено",
    },
    {
    "title": "Junior Python ",
    "company": "Roundls",
    "link": "https://jobs.roundls.edu/",
    "location": "Віддалено",
    }
]


@pytest.fixture()
def user():
    return User.objects.create_user(
        username="test", email="test@gmail.com", password="testpass",
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username="user2", email="user2@example.com", password="testpass"
    )


@pytest.fixture()
def vacancy():
    return Vacancy.objects.create(
        title="Junior Python Developer",
        company="Middels",
        link="https://jobs.middels.edu/",
        location="Віддалено",
        source=DOU,
    )


@pytest.fixture
def no_threads(monkeypatch):
    """Replace Thread, so no real background parsing starts."""
    fake_thread = Mock()
    monkeypatch.setattr(services.threading, "Thread", fake_thread)
    return fake_thread


@pytest.fixture
def recent_run():
    """A finished DOU run, just created: DOU is on cooldown."""
    return ParseRun.objects.create(source=DOU, status=ParseRun.Status.SUCCESS)


class TestIngestVacancies:
    @pytest.mark.django_db
    def test_saves_new_vacancies(self):
        count = ingest_vacancies(DOU, PARSED_ITEMS)
        assert count == 2
        assert Vacancy.objects.count() == 2

    @pytest.mark.django_db
    def test_skips_duplicates(self):
        ingest_vacancies(DOU, PARSED_ITEMS)
        count_dubl = ingest_vacancies(DOU, PARSED_ITEMS)
        assert count_dubl == 0
        assert Vacancy.objects.count() == 2


class TestSetVacaancyStatus:
    @pytest.mark.django_db
    def test_applied(self, user, vacancy, action=APPLIED):
        set_vacancy_status(user=user, vacancy=vacancy, action=action)

        state = UserVacancy.objects.get(user=user, vacancy=vacancy)
        assert state.applied is True
        assert state.is_irrelevant is False

    @pytest.mark.django_db
    def test_change_vacancy_status(self, user, vacancy):
        set_vacancy_status(user=user, vacancy=vacancy, action=APPLIED)
        set_vacancy_status(user=user, vacancy=vacancy, action=IRRELEVANT)

        state = UserVacancy.objects.get(user=user, vacancy=vacancy)
        assert state.applied is False
        assert state.is_irrelevant is True
        assert UserVacancy.objects.count() == 1

    @pytest.mark.django_db
    def test_reset(self, user, vacancy):
        set_vacancy_status(user=user, vacancy=vacancy, action=APPLIED)
        set_vacancy_status(user=user, vacancy=vacancy, action=RESET)

        state = UserVacancy.objects.get(user=user, vacancy=vacancy)
        assert state.applied is False
        assert state.is_irrelevant is False

    @pytest.mark.django_db
    def test_statuses_are_separate_for_each_user(self, user, other_user, vacancy):
        set_vacancy_status(user=user, vacancy=vacancy, action=APPLIED)
        set_vacancy_status(user=other_user, vacancy=vacancy, action=IRRELEVANT)

        first = UserVacancy.objects.get(user=user, vacancy=vacancy)
        second = UserVacancy.objects.get(user=other_user, vacancy=vacancy)
        assert UserVacancy.objects.count() == 2
        assert first.applied is True
        assert first.is_irrelevant is False
        assert second.applied is False
        assert second.is_irrelevant is True


class TestStartParse:
    @pytest.mark.django_db
    def test_guest_gets_default_period(self, no_threads):
        run = start_parse(user=None, source=DOU, days=30)

        run = ParseRun.objects.get(pk=run.pk)
        assert run.days == DEFAULT_DAYS
        assert run.started_by is None

    def test_start_parser_rejects_unknown_source(self):
        with pytest.raises(ParseNotAllowed):
            start_parse(None, "unknown")

    @pytest.mark.django_db
    def test_start_parse_rejects_invalid_period(self, user):
        invalid_day = 3
        with pytest.raises(ParseNotAllowed):
            start_parse(user=user, source=DOU, days=invalid_day)

    @pytest.mark.django_db
    def test_start_parse_rejects_run_during_cooldown(self,user):
        ParseRun.objects.create(
            source=DOU,
            started_by=user,
            status=ParseRun.Status.SUCCESS,
        )
        with pytest.raises(ParseNotAllowed):
            start_parse(user=user, source=DOU)

    @pytest.mark.django_db
    def test_start_parse_creates_running_record(self, monkeypatch, user):
        monkeypatch.setattr(services.threading, "Thread", Mock())
        run = start_parse(user=user, source=DOU)
        assert ParseRun.objects.get(pk=run.pk).status == ParseRun.Status.RUNNING
        assert ParseRun.objects.count() == 1


class TestExecuteRun:
    @pytest.mark.django_db
    def test_marks_run_as_success(self, monkeypatch):
        def fake_parser(days):
            return PARSED_ITEMS

        monkeypatch.setitem(services.PARSERS, DOU, fake_parser)
        run = ParseRun.objects.create(source=DOU)

        _execute_run(run.pk)

        run = ParseRun.objects.get(pk=run.pk)
        assert run.status == ParseRun.Status.SUCCESS
        assert run.new_count == 2
        assert run.finished_at is not None

    @pytest.mark.django_db
    def test_returns_error_and_failed_record(self, monkeypatch):
        def fake_parser(days):
            raise ParserError("test error")

        monkeypatch.setitem(services.PARSERS, DOU, fake_parser)
        run = ParseRun.objects.create(source=DOU)
        _execute_run(run.pk)
        run = ParseRun.objects.get(pk=run.pk)

        assert run.status == ParseRun.Status.FAILED
        assert run.error == "test error"
        assert run.finished_at is not None

    @pytest.mark.django_db
    def test_hides_technical_details_on_unexpected_error(self, monkeypatch):
        def fake_parser(days):
            raise ValueError("secret technical details")

        monkeypatch.setitem(services.PARSERS, DOU, fake_parser)
        run = ParseRun.objects.create(source=DOU)

        _execute_run(run.pk)

        run = ParseRun.objects.get(pk=run.pk)
        assert run.status == ParseRun.Status.FAILED
        assert run.error == "Внутрішня помилка"
        assert "secret" not in run.error
        assert run.finished_at is not None


class TestStartParseAll:
    @pytest.mark.django_db
    def test_skips_cooldown_source_and_starts_others(
        self, user, recent_run,no_threads
    ):
        started, skipped = start_parse_all(user=user)

        assert "DOU.ua" in skipped[0]
        assert "DOU.ua" not in started
        assert len(started) == 2
