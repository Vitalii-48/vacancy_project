from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import path

from .models import ParseRun, Vacancy
from .services import start_parse_all


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "link", "source", "applied", "is_irrelevant", "created_at")
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
        # Only a superuser may start parsers, a plain staff user may not.
        if not request.user.is_superuser:
            raise PermissionDenied

        # A request that changes data must be POST (a GET link can be forged).
        if request.method != "POST":
            return redirect("..")

        # Same cooldown and the same "one run per source" rule as on the site.
        started, skipped = start_parse_all(request.user)
        if started:
            self.message_user(request, f"Запущено: {', '.join(started)}.", messages.INFO)
        for text in skipped:
            self.message_user(request, text, messages.WARNING)
        return redirect("..")


@admin.register(ParseRun)
class ParseRunAdmin(admin.ModelAdmin):
    """Parse runs are history, so they are read-only."""

    list_display = ("source", "status", "started_by", "new_count", "created_at", "finished_at")
    list_filter = ("source", "status")
    readonly_fields = [f.name for f in ParseRun._meta.fields]

    def has_add_permission(self, request):
        return False