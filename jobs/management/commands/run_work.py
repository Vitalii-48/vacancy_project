# jobs\management\commands\run_work.py
from django.core.management.base import BaseCommand
from jobs.parsers.work import fetch_work
from jobs.models import Vacancy

class Command(BaseCommand):
    help = "Отримує вакансії з Work.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Work.ua...")
        works = fetch_work()
        saved = Vacancy.save_to_db("Work.ua", works)

        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(saved)} нових вакансій."))