# jobs\admin.py

from django.contrib import admin
from .models import Vacancy

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "source", "applied", "created_at")
    list_filter = ("applied", "source")
    search_fields = ("title", "company")
