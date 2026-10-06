import logging
import math
import threading
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from .exceptions import ParseNotAllowed, ParserError
from .filters import MAX_AGE_DAYS as DEFAULT_DAYS
from .models import ParseRun, UserVacancy, Vacancy
from .parsers.registry import PARSERS

logger = logging.getLogger(__name__)

# What each button does with the two flags.
STATUS_FIELDS = {
    "applied": {"applied": True, "is_irrelevant": False},
    "irrelevant": {"applied": False, "is_irrelevant": True},
    "reset": {"applied": False, "is_irrelevant": False},
}

# Pause between two runs of the same source.
COOLDOWN = timedelta(minutes=10)

# A run that stays "running" longer than this is considered dead (server restarted).
STALE_AFTER = timedelta(minutes=15)

# Period choices: key -> (label shown to the user, number of days back).
# Only these values are accepted, so nothing else can come from the form.
PERIODS = {
    "two_days": ("Сьогодні і вчора", 1),
    "week": ("7 днів", 7),
    "two_weeks": ("14 днів", 14),
    "month": ("Місяць (30 днів)", 30),
}
DEFAULT_PERIOD = "week"
ALLOWED_DAYS = {period_days for _, period_days in PERIODS.values()}


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


def start_parse(user, source: str, days: int = DEFAULT_DAYS) -> ParseRun:
    """Start parsing ONE source in a background thread."""
    # Accept only known sources.
    if source not in PARSERS:
        raise ParseNotAllowed("Невідоме джерело.")

    # Only logged-in users may change the period; guests always get the default.
    is_logged_in = user is not None and user.is_authenticated
    if not is_logged_in:
        days = DEFAULT_DAYS

    # Never trust the form: accept only the known periods.
    if days not in ALLOWED_DAYS:
        raise ParseNotAllowed("Невірний період.")

    now = timezone.now()

    # Dead runs would block the source forever, so close them first.
    ParseRun.objects.filter(
        source=source,
        status=ParseRun.Status.RUNNING,
        created_at__lt=now - STALE_AFTER,
    ).update(status=ParseRun.Status.FAILED, error="Timed out", finished_at=now)

    # Cooldown: the last run of this source must be old enough.
    last = ParseRun.objects.filter(source=source).first()
    if last and last.created_at > now - COOLDOWN:
        seconds = (last.created_at + COOLDOWN - now).total_seconds()
        raise ParseNotAllowed(
            f"Це джерело вже запускали нещодавно. Спробуйте через {math.ceil(seconds / 60)} хв."
        )

    # The database allows only one "running" row per source (see the constraint).
    started_by = user if is_logged_in else None
    try:
        with transaction.atomic():
            run = ParseRun.objects.create(source=source, started_by=started_by, days=days)
    except IntegrityError:
        raise ParseNotAllowed("Це джерело вже обробляється.") from None

    threading.Thread(target=_execute_run, args=(run.pk,), daemon=True).start()
    return run


def _execute_run(run_id: int) -> None:
    """Run the parser and save the result. Works in a background thread."""
    run = ParseRun.objects.get(pk=run_id)
    try:
        items = PARSERS[run.source](days=run.days)
        run.new_count = ingest_vacancies(run.source, items)
        run.status = ParseRun.Status.SUCCESS
    except ParserError as e:
        # Our own message: safe to store and show.
        run.status = ParseRun.Status.FAILED
        run.error = str(e)[:255]
    except Exception:  # noqa: BLE001 - a thread must never die silently
        logger.exception("Unexpected error in run %s", run_id)
        run.status = ParseRun.Status.FAILED
        run.error = "Внутрішня помилка"  # no technical details for the user
    finally:
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "new_count", "error", "finished_at"])
        # Every thread has its own database connection: close it.
        connection.close()


def start_parse_all(user, days: int = DEFAULT_DAYS) -> tuple[list[str], list[str]]:
    """Start every source. Return (started labels, skipped messages)."""
    started, skipped = [], []
    for source in PARSERS:
        label = Vacancy.Source(source).label
        try:
            start_parse(user, source, days)
        except ParseNotAllowed as e:
            # One source on cooldown must not block the others.
            skipped.append(f"{label}: {e}")
        else:
            started.append(label)
    return started, skipped