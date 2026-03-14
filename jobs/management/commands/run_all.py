# jobs\management\commands\run_all.py

from django.core.management.base import BaseCommand
from jobs.parsers.jooble import fetch_joobl
from jobs.parsers.robota import fetch_robota
from jobs.parsers.work import fetch_work
from jobs.parsers.dou import fetch_dou_rss
from jobs.models import Vacancy

class Command(BaseCommand):
    help = "Запуск усіх парсерів (Jooble, Robota.ua, Work.ua, DOU.ua)"

    def handle(self, *args, **options):
        sources = [
            ("Jooble.ua", fetch_joobl),
            ("Robota.ua", fetch_robota),
            ("Work.ua", fetch_work),
            ("DOU.ua", fetch_dou_rss),
        ]

        for source_name, fetch_func in sources:
            self.stdout.write(f"⏳ Звертаюсь до {source_name}...")
            jobs = fetch_func()
            if jobs:  # ✅ тільки якщо є вакансії
                saved = Vacancy.save_to_db(source_name, jobs)
                if saved:
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Збережено {len(saved)} нових вакансій з {source_name}"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Усі {len(jobs)} вакансій з {source_name} вже були в базі"
                    ))

            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Нічого не знайдено на {source_name}"))

        self.stdout.write(self.style.SUCCESS("🎉 Усі парсери виконані"))