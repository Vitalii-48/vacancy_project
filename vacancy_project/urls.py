# vacancy_project\urls.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .views import guest_login
from django.http import HttpResponse
import vacancy_project.admin

urlpatterns = [
    path('', lambda request: redirect('/admin/')),
    path('admin/', admin.site.urls),
    path('demo/', guest_login, name='guest_login'),
    path('ping/', lambda request: HttpResponse('ok'))
]