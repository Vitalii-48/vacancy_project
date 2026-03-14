# vacancy_project\views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect

def guest_login(request):
    user = authenticate(username='guest', password='guestpassword123')
    if user is not None:
        login(request, user)
    return redirect('/admin/jobs/vacancy/')