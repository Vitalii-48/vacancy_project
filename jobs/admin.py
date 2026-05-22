# jobs\admin.py

import threading
from django.urls import path
from django.contrib import admin
from django.core.management import call_command
from django.contrib import messages
from django.shortcuts import redirect
from .models import Vacancy

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "link", "source", "applied",  "is_irrelevant", "created_at")
    list_filter = ("applied", "source")
    list_editable = ("applied", "is_irrelevant")
    search_fields = ("title", "company")
    change_list_template = "admin/jobs/vacancy/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("run-parsers/", self.admin_site.admin_view(self.run_parsers)),
        ]
        return custom_urls + urls

    def run_parsers(self, request):
        # Функція-обгортка для запуску команди
        def run_in_background():
            call_command('run_all')

        # Створюємо і запускаємо потік
        thread = threading.Thread(target=run_in_background)
        thread.start()

        # Миттєво повідомляємо користувача
        self.message_user(
            request,
            "Парсери запущені у фоновому режимі. Вакансії з'являться в базі за декілька хвилин.",
            messages.INFO
        )
        return redirect("..")