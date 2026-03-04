# jobs\management\commands\run_work.py
from django.core.management.base import BaseCommand
from jobs.parsers.work import fetch_work   # імпортуємо твій скрапер

class Command(BaseCommand):
    help = "Отримує вакансії з Work.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Work.ua...")
        works = fetch_work()
        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(works)} вакансій."))