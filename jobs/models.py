from django.conf import settings
from django.db import models


class Vacancy(models.Model):
    """One job vacancy. The data is the same for all users."""

    class Source(models.TextChoices):
        # Allowed sources: (value in database, name for people).
        JOOBLE = "Jooble.ua", "Jooble"
        ROBOTA = "Robota.ua", "Robota.ua"
        WORK = "Work.ua", "Work.ua"
        DOU = "DOU.ua", "DOU.ua"

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="Remote")
    # Link is unique, so the same vacancy is never saved twice.
    link = models.URLField(max_length=500, unique=True)
    source = models.CharField(max_length=50, choices=Source.choices)
    # Temporary: the Telegram bot still uses these two fields.
    # Later the statuses will live only in UserVacancy.
    applied = models.BooleanField(default=False)  # I already applied
    is_irrelevant = models.BooleanField(default=False)  # not interesting
    created_at = models.DateTimeField(auto_now_add=True)  # when we saved it

    class Meta:
        ordering = ["-created_at"]  # newest vacancies first
        # Index makes search by source and date fast.
        indexes = [models.Index(fields=["source", "-created_at"])]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class UserVacancy(models.Model):
    """Status of one vacancy for one user (applied, not interesting)."""

    # Who this status belongs to. If the user is deleted, the status is deleted.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vacancy_states",
    )
    # Which vacancy this status is about.
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name="user_states",
    )
    applied = models.BooleanField(default=False)
    is_irrelevant = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)  # changes on every save

    class Meta:
        # One user can have only one status for one vacancy.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "vacancy"], name="unique_user_vacancy"
            ),
        ]
        # Index makes "my applied vacancies" search fast.
        indexes = [models.Index(fields=["user", "applied", "is_irrelevant"])]

    def __str__(self):
        return f"{self.user} → {self.vacancy}"


class ParseRun(models.Model):
    """One run of a parser. Used for status and for the cooldown."""

    class Status(models.TextChoices):
        RUNNING = "running", "Виконується"
        SUCCESS = "success", "Успішно"
        FAILED = "failed", "Помилка"

    source = models.CharField(max_length=50, choices=Vacancy.Source.choices)
    # Who started it. Empty for a guest. Keep the run if the user is deleted.
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="parse_runs",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.RUNNING
    )
    days = models.PositiveSmallIntegerField(default=7)  # how many last days
    keyword = models.CharField(max_length=50, blank=True)
    new_count = models.PositiveIntegerField(default=0)  # new vacancies saved
    # Short and safe text. Never put a technical error here.
    error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        # Fast search: "last run of this source".
        indexes = [models.Index(fields=["source", "-created_at"])]
        # At most ONE "running" row per source, checked by the database.
        constraints = [
            models.UniqueConstraint(
                fields=["source"],
                condition=models.Q(status="running"),
                name="one_running_parse_per_source",
            ),
        ]
    def __str__(self):
        return f"{self.source} {self.status} {self.created_at:%d.%m %H:%M}"