# jobs\management\commands\run_robota.py
from django.core.management.base import BaseCommand
from jobs.parsers.robota import fetch_robota   # імпортуємо твій скрапер

class Command(BaseCommand):
    help = "Отримує вакансії з Robota.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Robota.ua...")
        jobs =  fetch_robota()
        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(jobs)} вакансій."))