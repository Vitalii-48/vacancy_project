# jobs\management\commands\run_all.py

import asyncio
from django.core.management.base import BaseCommand
from jobs.parsers.jooble import save_job_to_db as run_jooble
from jobs.parsers.robota import save_job_to_db as run_robota
from jobs.parsers.work import save_work_to_db as run_work

class Command(BaseCommand):
    help = "Запуск усіх парсерів (Jooble, Robota.ua, Work.ua)"

    def handle(self, *args, **options):
        run_jooble()
        run_robota()
        run_work()
        self.stdout.write(self.style.SUCCESS("🎉 Усі парсери виконані"))