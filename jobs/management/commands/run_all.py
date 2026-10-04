import logging

from django.core.management.base import BaseCommand

from jobs.parsers.jooble import fetch_joobl
from jobs.parsers.robota import fetch_robota
from jobs.parsers.work import fetch_work
from jobs.parsers.dou import fetch_dou_rss
from jobs.exceptions import ParserError
from jobs.models import Vacancy
from jobs.services import ingest_vacancies

logger = logging.getLogger(__name__)

PARSERS = [
    (Vacancy.Source.JOOBLE, fetch_joobl),
    #(Vacancy.Source.ROBOTA, fetch_robota),  # Cloudflare blok
    (Vacancy.Source.WORK, fetch_work),
    (Vacancy.Source.DOU, fetch_dou_rss),
]

class Command(BaseCommand):
    help = "Запуск усіх парсерів (Jooble, Robota.ua, Work.ua, DOU.ua)"

    def handle(self, *args, **options):

        for source, fetch in PARSERS:
            self.stdout.write(f"Звертаюсь до {source}...")
            try:
                count = ingest_vacancies(source, fetch())
            except ParserError as e:
                logger.error("Parser failed: %s: %s", source, e)
                self.stdout.write(self.style.ERROR(f"{source.label}: {e}"))
                continue
            except Exception:
                logger.exception("Unexpected error: %s", source)
                self.stdout.write(self.style.ERROR(f"{source.label}: баг у коді, дивіться логи"))
                continue
            self.stdout.write(self.style.SUCCESS(f"{source.label}: {count} нових"))
        self.stdout.write(self.style.SUCCESS("Усі парсери виконані"))
