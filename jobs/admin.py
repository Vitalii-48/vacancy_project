from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q

User = get_user_model()

# Replace the default user admin with our own.
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username", "email", "first_name",
        "date_joined", "last_login",
        "is_active", "is_staff",
        "applied_count", "irrelevant_count", "runs_count",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "first_name")
    ordering = ("-date_joined",)
    list_per_page = 25

    def get_queryset(self, request):
        # Count related rows in ONE query instead of one query per user.
        # distinct=True is required: several joins would multiply the counts.
        return super().get_queryset(request).annotate(
            _applied=Count("vacancy_states", filter=Q(vacancy_states__applied=True), distinct=True),
            _irrelevant=Count("vacancy_states", filter=Q(vacancy_states__is_irrelevant=True), distinct=True),
            _runs=Count("parse_runs", distinct=True),
        )

    @admin.display(description="Відгуків", ordering="_applied")
    def applied_count(self, obj):
        return obj._applied

    @admin.display(description="Нерелевантних", ordering="_irrelevant")
    def irrelevant_count(self, obj):
        return obj._irrelevant

    @admin.display(description="Запусків парсингу", ordering="_runs")
    def runs_count(self, obj):
        return obj._runs