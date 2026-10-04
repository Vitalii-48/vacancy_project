from django.db import transaction

from .models import Vacancy


@transaction.atomic
def ingest_vacancies(source: str, items: list[dict]) -> int:
    """Зберігає нові вакансії з парсера. Повертає кількість нових."""
    unique = {item["link"]: item for item in items}  # прибираємо дублі в самій пачці

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
    Vacancy.objects.bulk_create(new, ignore_conflicts=True)
    return len(new)