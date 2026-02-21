# management\commands\run_jooble.py

import requests, telebot
import subprocess
from decouple import config
from django.core.management.base import BaseCommand
from django.conf import settings
from jobs.models import Vacancy

class Command(BaseCommand):
    help = "Отримує вакансії з Jooble API та зберігає в БД"

    def handle(self, *args, **options):
        api_key = settings.JOOBLE_API_KEY  # ключ беремо з settings.py
        url = f"https://ua.jooble.org/api/{api_key}"

        payload = {
            "keywords": "Python developer",
            "location": "Remote"
        }

        self.stdout.write("⏳ Звертаюсь до Jooble API...")

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            jobs = data.get('jobs', [])
            new_count = 0

            for job in jobs:
                title = job.get("title", "").lower()
                snippet = job.get("snippet", "").lower()

                # ❌ Пропускаємо вакансії, де є Senior або Middle
                if "senior" in title or "middle" in title or "senior" in snippet or "middle" in snippet:
                    continue

                vacancy, created = Vacancy.objects.get_or_create(
                    link=job.get('link'),
                    defaults={
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location', 'Remote'),
                        'source': 'Jooble',
                        'is_sent': False
                    }
                )
                if created:
                    new_count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ Готово! Додано {new_count} нових вакансій."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Помилка: {e}"))

        self.stdout.write(self.style.SUCCESS("🚀 Запускаю Telegram‑бота..."))
        subprocess.run(["python", "telegram_bot/bot.py"])
