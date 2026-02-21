# telegram_bot\bot.py

import telebot
from telebot import types
from decouple import config
import os
import sys
import django


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vacancy_project.settings")
django.setup()

from jobs.models import Vacancy
bot = telebot.TeleBot(config("TELEGRAM_BOT_TOKEN"))


@bot.message_handler(commands=["vacancies"])
def send_vacancies(message):
    vacancies = Vacancy.objects.order_by("-created_at")[:5]
    print(f"DEBUG: Знайдено вакансій: {vacancies.count()}")

    for v in vacancies:
        text = f"{v.id}. {v.title} @ {v.company} ({v.location}) {'✅' if v.applied else '➖'}\n{v.link}"

        # створюємо inline‑кнопку
        markup = types.InlineKeyboardMarkup()
        if not v.applied:
            markup.add(types.InlineKeyboardButton("✅ Відгукнутись", callback_data=f"apply_{v.id}"))
        else:
            markup.add(types.InlineKeyboardButton("🔄 Скасувати відгук", callback_data=f"unapply_{v.id}"))

        bot.send_message(message.chat.id, text, reply_markup=markup)


# обробка натискань на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("apply_") or call.data.startswith("unapply_"))
def callback_apply(call):
    vacancy_id = int(call.data.split("_")[1])
    vacancy = Vacancy.objects.get(id=vacancy_id)

    if call.data.startswith("apply_"):
        vacancy.applied = True
        vacancy.save()
        bot.answer_callback_query(call.id, f"Вакансія {vacancy.title} відзначена як відгукнута ✅")
    elif call.data.startswith("unapply_"):
        vacancy.applied = False
        vacancy.save()
        bot.answer_callback_query(call.id, f"Вакансія {vacancy.title} повернена у статус ➖")

    # оновлюємо повідомлення з новим статусом
    new_text = f"{vacancy.id}. {vacancy.title} @ {vacancy.company} ({vacancy.location}) {'✅' if vacancy.applied else '➖'}\n{vacancy.link}"
    markup = types.InlineKeyboardMarkup()
    if not vacancy.applied:
        markup.add(types.InlineKeyboardButton("✅ Відгукнутись", callback_data=f"apply_{vacancy.id}"))
    else:
        markup.add(types.InlineKeyboardButton("🔄 Скасувати відгук", callback_data=f"unapply_{vacancy.id}"))

    bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
@bot.message_handler(commands=["applied"])
def mark_applied(message):
    try:
        vacancy_id = int(message.text.split()[1])
        vacancy = Vacancy.objects.get(id=vacancy_id)
        vacancy.applied = True
        vacancy.save()
        bot.send_message(message.chat.id, f"Вакансія '{vacancy.title}' відзначена як відгукнута ✅")
    except Exception:
        bot.send_message(message.chat.id, "Помилка: вкажи ID вакансії після команди /applied")

if __name__ == "__main__":
    bot.polling(none_stop=True)
