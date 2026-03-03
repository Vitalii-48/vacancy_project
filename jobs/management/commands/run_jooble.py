# jobs\management\commands\run_jooble.py
from django.core.management.base import BaseCommand
from jobs.parsers.jooble import save_job_to_db

class Command(BaseCommand):
    help = "Отримує вакансії з Jooble API та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Jooble API...")
        jobs = save_job_to_db()
        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(jobs)} нових вакансій."))

