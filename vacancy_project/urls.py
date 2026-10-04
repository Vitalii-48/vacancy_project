from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

import vacancy_project.admin  # noqa: F401  (sets the admin site titles)
from jobs.views import run_parse, run_parse_all, set_status, vacancy_list

urlpatterns = [
    path("", vacancy_list, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("vacancies/<int:vacancy_id>/status/", set_status, name="set_status"),
    path("parse/", run_parse, name="run_parse"),
    path("parse/all/", run_parse_all, name="run_parse_all"),
    path("ping/", lambda request: HttpResponse("ok")),
]