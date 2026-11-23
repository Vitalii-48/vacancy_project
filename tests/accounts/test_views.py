import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="test",
        email="test@gmail.com",
        password="TestPass123!",
    )
@pytest.mark.django_db
def test_authenticated_user_redirect_home(client, user):
    client.force_login(user)
    response = client.get(reverse("register"))

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def  test_guest_on_register(client):
    response = client.get(reverse("register"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_guest_can_register_and_logs_in(client):
    response = client.post(reverse("register"), {
    "username": "newuser",
    "email": "new@gmail.com",
    "password1": "TestPass123!",
    "password2": "TestPass123!",
})

    assert response.status_code == 302
    assert response.url == reverse("home")
    assert User.objects.filter(username="newuser").exists()
    assert response.wsgi_request.user.is_authenticated is True


@pytest.mark.django_db
def test_guest_cannot_register_without_email(client):
    response = client.post(reverse("register"), {
        "username": "newuser",
        "email": "",
        "password1": "TestPass123!",
        "password2": "TestPass123!",
    })

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert not User.objects.filter(username="newuser").exists()