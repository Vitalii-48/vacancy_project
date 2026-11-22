import pytest

from accounts.forms import RegisterForm, User


@pytest.fixture()
def user():
    return User.objects.create_user(
        username="test", email="test@gmail.com", password="testpass",
    )

@pytest.mark.django_db
def test_form_email_lower():
    form = RegisterForm(data={
        "username": "tester",
        "email": "TEST@GMAIL.COM",
        "password1": "TestPass123!",
        "password2": "TestPass123!",
    })

    assert form.is_valid() is True
    assert form.cleaned_data["email"] == "test@gmail.com"


@pytest.mark.django_db
def test_form_duplicate_email(user):
    form = RegisterForm(data={
        "username": "tester",
        "email": "TEST@GMAIL.COM",
        "password1": "TestPass123!",
        "password2": "TestPass123!",
    })

    assert form.is_valid() is False
    assert "email" in form.errors
