import logging

from django.db import transaction

from .models import UserVacancy, Vacancy

logger = logging.getLogger(__name__)

# What each button does with the two flags.
STATUS_FIELDS = {
    "applied": {"applied": True, "is_irrelevant": False},
    "irrelevant": {"applied": False, "is_irrelevant": True},
    "reset": {"applied": False, "is_irrelevant": False},
}


@transaction.atomic
def ingest_vacancies(source: str, items: list[dict]) -> int:
    """Save new vacancies from a parser. Return how many are new."""
    # Remove duplicates inside the batch.
    unique = {item["link"]: item for item in items}

    # One query: which links are already in the database.
    existing = set(
        Vacancy.objects.filter(link__in=unique).values_list("link", flat=True)
    )
    new = [
        Vacancy(
            source=source,
            link=link,
            title=item["title"][:255],
            company=item["company"][:255],
            location=item.get("location", "Remote")[:255],
        )
        for link, item in unique.items()
        if link not in existing
    ]
    # One query for all new vacancies; ignore_conflicts skips duplicates.
    Vacancy.objects.bulk_create(new, ignore_conflicts=True)
    logger.info("Source %s: received %d, new %d", source, len(unique), len(new))
    return len(new)


@transaction.atomic
def set_vacancy_status(user, vacancy: Vacancy, action: str) -> None:
    """Set the status of a vacancy for ONE user."""
    # Create the row if it does not exist, otherwise update it.
    UserVacancy.objects.update_or_create(
        user=user,
        vacancy=vacancy,
        defaults=STATUS_FIELDS[action],
    )