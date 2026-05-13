# jobs\management\commands\run_jooble.py
from django.core.management.base import BaseCommand
from jobs.parsers.jooble import fetch_joobl
from jobs.models import Vacancy


class Command(BaseCommand):
    help = "Отримує вакансії з Jooble API та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Jooble API...")
        jobs = fetch_joobl()
        saved = Vacancy.save_to_db("Jooble.ua", jobs)

        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(saved)} нових вакансій."))

