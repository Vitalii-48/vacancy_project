# vacancy_project\views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from decouple import config

username = config('USERNAME_GUEST')
password = config('PASSWORD_GUEST')
def guest_login(request):
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
    return redirect('/admin/jobs/vacancy/')