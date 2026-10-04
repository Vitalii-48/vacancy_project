# jobs/management/commands/run_all.py
# Command: run all parsers one after another.

import logging

from django.core.management.base import BaseCommand

from jobs.exceptions import ParserError
from jobs.models import Vacancy
from jobs.parsers.registry import PARSERS
from jobs.services import ingest_vacancies

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run all parsers"

    def handle(self, *args, **options):
        for value, fetch in PARSERS.items():
            label = Vacancy.Source(value).label
            self.stdout.write(f"⏳ {label}...")
            try:
                count = ingest_vacancies(value, fetch())
            except ParserError as e:
                # Expected failure: a short message is enough.
                logger.error("Parser failed: %s: %s (cause: %r)", value, e, e.__cause__)
                self.stdout.write(self.style.ERROR(f"{label}: {e}"))
                continue
            except Exception:  # noqa: BLE001 - last safety net, one source must not stop the others
                logger.exception("Unexpected error: %s", value)
                self.stdout.write(self.style.ERROR(f"{label}: баг у коді, дивіться логи"))
                continue
            self.stdout.write(self.style.SUCCESS(f"{label}: {count} нових"))