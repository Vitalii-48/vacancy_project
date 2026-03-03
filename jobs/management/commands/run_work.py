# jobs\management\commands\run_work.py
from django.core.management.base import BaseCommand
from jobs.parsers.work import save_work_to_db   # імпортуємо твій скрапер

class Command(BaseCommand):
    help = "Отримує вакансії з Work.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Work.ua...")
        works = save_work_to_db()
        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(works)} вакансій."))