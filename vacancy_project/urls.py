# vacancy_project\urls.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

# Функція для перенаправлення
def redirect_to_admin(request):
    return redirect('admin/')

urlpatterns = [
    path('', redirect_to_admin), # Пустий який веде в адмінку
    path('admin/', admin.site.urls),
]