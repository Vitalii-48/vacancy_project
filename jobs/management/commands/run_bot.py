# jobs\management\commands\run_bot.py
from django.core.management.base import BaseCommand
from telegram_bot.bot import bot

class Command(BaseCommand):
    help = "Запуск Telegram‑бота"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Telegram‑бота запущено..."))
        bot.polling(none_stop=True)
