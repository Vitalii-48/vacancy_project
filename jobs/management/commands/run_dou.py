# jobs\management\commands\run_dou.py

from django.core.management.base import BaseCommand
from jobs.parsers.dou import fetch_dou_rss
from jobs.models import Vacancy


class Command(BaseCommand):
    help = "Отримує вакансії з DOU.ua та зберігає в БД"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до DOU.ua...")
        jobs = fetch_dou_rss()
        saved = Vacancy.save_to_db("DOU.ua", jobs)

        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {len(saved)} нових вакансій."))