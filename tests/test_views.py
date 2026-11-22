from unittest.mock import Mock
from urllib import request

import pytest

from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse

from jobs.exceptions import ParseNotAllowed
from  jobs.models import Vacancy, UserVacancy
from jobs.services import DEFAULT_PERIOD, PERIODS
from jobs.views import _read_days, set_status

User = get_user_model()

# Names of the actions that set_vacancy_status accepts.
APPLIED = "applied"
IRRELEVANT = "irrelevant"
RESET = "reset"

@pytest.fixture()
def user():
    return User.objects.create_user(
        username="test", email="test@gmail.com", password="testpass",
    )

@pytest.fixture()
def vacancy():
    return Vacancy.objects.create(
        title="Junior Python Developer",
        company="Middels",
        link="https://jobs.middels.edu/",
        location="Віддалено",
        source=Vacancy.Source.DOU.value,
    )

@pytest.fixture()
def second_vacancy():
    return Vacancy.objects.create(
        title="Junior Developer",
        company="Roundls",
        link="https://jobs.roundls.edu/",
        location="Дистанційно",
        source=Vacancy.Source.WORK.value,
    )


@pytest.mark.django_db
def test_guest_sees_single_vacancy_when_multiple_sources_exist(
        client, vacancy, second_vacancy
):

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert response.context["source"] == Vacancy.Source.DOU
    assert len(response.context["page_obj"]) == 1
    assert Vacancy.objects.count() == 2

@pytest.mark.django_db
def test_verification_of_valid_status(client, user):
    client.force_login(user)
    response = client.get(reverse("home"), {"status": "invalid_status"})

    assert response.context["status"] == "all"


def test_period_verification():
    request = Mock()
    request.POST = {"period": "week"}
    assert _read_days(request) == 7

def test_period_default():
    request = Mock()
    request.POST = {}
    assert _read_days(request) == PERIODS[DEFAULT_PERIOD][1]

def test_period_invalid():
    request = Mock()
    request.POST = {"period": "test"}

    with pytest.raises(ParseNotAllowed):
        _read_days(request)


# set_status    ===============
@pytest.mark.django_db
def test_check_action(client, user, vacancy):
    client.force_login(user)
    response = client.post(reverse("set_status", args=[vacancy.pk]),
                        {"action": "unknown"})

    assert response.status_code == 400

@pytest.mark.django_db
def test_valid_action(client, user, vacancy):
    client.force_login(user)
    response = client.post(reverse("set_status", args=[vacancy.pk]),
                        {"action": "applied"})

    assert response.status_code == 302

@pytest.mark.django_db
def test_guest_cannot_set_status(client, user, vacancy):
    response = client.post(
        reverse("set_status", args=[vacancy.pk]),
        {"action": "applied"},
    )

    assert response.status_code == 302

@pytest.mark.django_db
def test_404(client, user, vacancy):
    client.force_login(user)
    missing_id = vacancy.pk + 1
    response = client.post(
        reverse("set_status", args=[missing_id]),
        {"action": "applied"},
    )

    assert response.status_code == 404

@pytest.mark.django_db
def test_set_status_redirects_to_safe_next(client, user, vacancy):
    client.force_login(user)
    response = client.post(
        reverse("set_status", args=[vacancy.pk]),
        {"action": "applied", "next": "/?source=dou"},
    )

    assert response.status_code == 302
    assert response["Location"] == "/?source=dou"

@pytest.mark.django_db
def test_set_status_blocks_external_next(client, user, vacancy):
    client.force_login(user)
    response = client.post(
        reverse("set_status", args=[vacancy.pk]),
        {"action": "applied", "next": "https://evil.com"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("home")




