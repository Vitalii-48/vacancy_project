# Run the Robota.ua parser by hand. Local use only:
# it needs a browser, and Cloudflare lets it in only sometimes.

from django.core.management.base import BaseCommand

from jobs.exceptions import ParserError
from jobs.models import Vacancy
from jobs.parsers.robota import fetch_robota
from jobs.services import ingest_vacancies


class Command(BaseCommand):
    help = "Run the Robota.ua parser by hand (local use only)"

    def handle(self, *args, **options):
        try:
            items = fetch_robota()
        except ParserError as e:
            self.stdout.write(self.style.ERROR(f" Robota.ua: {e}"))
            return
        count = ingest_vacancies(Vacancy.Source.ROBOTA.value, items)
        self.stdout.write(self.style.SUCCESS(f"Robota.ua: {count} нових"))