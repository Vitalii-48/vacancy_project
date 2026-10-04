from django.db.models import Exists, OuterRef

from .models import UserVacancy, Vacancy, ParseRun

# Allowed values of the status filter.
VALID_STATUSES = {"all", "applied", "unapplied", "irrelevant"}


def get_vacancies(user=None, source: str | None = None, status: str = "all"):
    """Vacancies, newest first. A logged-in user can filter by status."""
    qs = Vacancy.objects.all()
    if source:
        qs = qs.filter(source=source)

    # A guest has no statuses, so no status filter.
    if user is None or not user.is_authenticated:
        return qs

    states = UserVacancy.objects.filter(user=user, vacancy=OuterRef("pk"))
    qs = qs.annotate(
        user_applied=Exists(states.filter(applied=True)),
        user_irrelevant=Exists(states.filter(is_irrelevant=True)),
    )

    if status == "applied":
        return qs.filter(user_applied=True)
    if status == "unapplied":
        return qs.filter(user_applied=False, user_irrelevant=False)
    if status == "irrelevant":
        return qs.filter(user_irrelevant=True)
    # "all": hide the irrelevant ones.
    return qs.filter(user_irrelevant=False)


def get_available_sources() -> list[tuple[str, str]]:
    """Sources that really have vacancies: [(value, label), ...]."""
    # order_by is required, otherwise distinct() does not remove duplicates.
    values = Vacancy.objects.order_by("source").values_list("source", flat=True).distinct()
    labels = dict(Vacancy.Source.choices)
    return [(value, labels.get(value, value)) for value in values]


def get_last_run(source: str):
    """Latest parse run of a source, or None."""
    return ParseRun.objects.filter(source=source).first()