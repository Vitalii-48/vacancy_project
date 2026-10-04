from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

import vacancy_project.admin  # noqa: F401  (заголовки адмінки)
from jobs.views import set_status, vacancy_list

from .views import guest_login

urlpatterns = [
    path("", vacancy_list, name="home"),    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("demo/", guest_login, name="guest_login"),
    path("ping/", lambda request: HttpResponse("ok")),
    path("vacancies/<int:vacancy_id>/status/", set_status, name="set_status"),
]