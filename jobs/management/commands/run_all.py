# jobs\management\commands\run_all.py

from django.core.management.base import BaseCommand
from jobs.parsers.jooble import fetch_joobl as run_jooble
from jobs.parsers.robota import fetch_robota as run_robota
from jobs.parsers.work import fetch_work as run_work
from jobs.parsers.dou import fetch_dou_rss as run_dou


class Command(BaseCommand):
    help = "Запуск усіх парсерів (Jooble, Robota.ua, Work.ua, DOU.ua)"

    def handle(self, *args, **options):
        self.stdout.write("⏳ Звертаюсь до Joble.ua...")
        run_jooble()
        self.stdout.write("⏳ Звертаюсь тепер до Robota.ua...")
        run_robota()
        self.stdout.write("⏳ Звертаюсь тепер до Work.ua...")
        run_work()
        self.stdout.write("⏳ Звертаюсь тепер до DOU.ua...")
        run_dou()
        self.stdout.write(self.style.SUCCESS("🎉 Усі парсери виконані"))