# jobs\management\commands\run_robota.py
from django.core.management.base import BaseCommand
from jobs.parsers.robota import save_job_to_db   # імпортуємо твій скрапер

class Command(BaseCommand):
    help = "Отримує вакансії з Robota.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Robota.ua...")
        jobs =  save_job_to_db()
        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(jobs)} вакансій."))