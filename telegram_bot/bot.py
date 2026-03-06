# telegram_bot\bot.py

import telebot
from telebot import types
from decouple import config
import os
import sys
import django

# Ініціалізація Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vacancy_project.settings")
django.setup()

from jobs.models import Vacancy

bot = telebot.TeleBot(config("TELEGRAM_BOT_TOKEN"))

# --- Крок 1: вибір джерела ---
@bot.message_handler(commands=["vacancies"])
def choose_source(message):
    # отримуємо унікальні джерела з таблиці Vacancy
    sources = Vacancy.objects.values_list("source", flat=True).distinct()

    markup = types.InlineKeyboardMarkup(row_width=len(sources))

    # перший рядок — кнопка "Всі джерела"
    markup.add(types.InlineKeyboardButton("🌐 Всі джерела", callback_data="source_all"))

    # другий рядок — усі джерела з бази
    buttons = [types.InlineKeyboardButton(f"🌐 {src}", callback_data=f"source_{src}") for src in sources]
    markup.row(*buttons)

    bot.send_message(message.chat.id, "Оберіть джерело вакансій:", reply_markup=markup)

# --- Крок 2: вибір статусу ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("source_"))
def choose_status(call):
    source = call.data.split("_", 1)[1]  # all, Work.ua, Robota.ua, Jooble, DOU

    markup = types.InlineKeyboardMarkup()
    # перший рядок — одна кнопка "Всі"
    markup.add(types.InlineKeyboardButton("📋 Всі", callback_data=f"status_{source}_all"))

    # другий рядок — дві кнопки поруч
    markup.row(
        types.InlineKeyboardButton("✅ Відгукнуті", callback_data=f"status_{source}_applied"),
        types.InlineKeyboardButton("➖ Не відгукнуті", callback_data=f"status_{source}_unapplied"),
    )

    bot.edit_message_text("Оберіть статус вакансій:", call.message.chat.id, call.message.message_id,
                          reply_markup=markup)


# --- Крок 3: показ вакансій ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("status_"))
def show_vacancies(call):
    _, source, status = call.data.split("_")

    # Фільтр по джерелу
    if source == "all":
        qs = Vacancy.objects.all()
    else:
        qs = Vacancy.objects.filter(source=source)

    # Фільтр по статусу
    if status == "applied":
        qs = qs.filter(applied=True)
    elif status == "unapplied":
        qs = qs.filter(applied=False)

    vacancies = qs.order_by("-created_at")

    if not vacancies.exists():
        bot.send_message(call.message.chat.id, "❌ Вакансій не знайдено.")
        return

    bot.send_message(call.message.chat.id, f"🔎 Знайдено {vacancies.count()} вакансій:")

    for v in vacancies:
        text = (
            f"{v.id}. {v.title} @ {v.company} ({v.location})\n"
            f"Джерело: {v.source}\n"
            f"Статус: {'✅ Відгукнута' if v.applied else '➖ Не відгукнута'}\n"
            f"{v.link}"
        )
        markup = types.InlineKeyboardMarkup()
        if not v.applied:
            markup.add(types.InlineKeyboardButton("✅ Відгукнутись", callback_data=f"apply_{v.id}"))
        else:
            markup.add(types.InlineKeyboardButton("🔄 Скасувати відгук", callback_data=f"unapply_{v.id}"))

        # Кнопка повернення до меню
        markup.add(types.InlineKeyboardButton("🔄 Повернутись до вибору джерела", callback_data="back_to_source"))

        bot.send_message(call.message.chat.id, text, reply_markup=markup)


# --- Apply / Unapply ---
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

    # Оновлення повідомлення
    new_text = (
        f"{vacancy.id}. {vacancy.title} @ {vacancy.company} ({vacancy.location})\n"
        f"Джерело: {vacancy.source}\n"
        f"Статус: {'✅ Відгукнута' if vacancy.applied else '➖ Не відгукнута'}\n"
        f"{vacancy.link}"
    )
    markup = types.InlineKeyboardMarkup()
    if not vacancy.applied:
        markup.add(types.InlineKeyboardButton("✅ Відгукнутись", callback_data=f"apply_{vacancy.id}"))
    else:
        markup.add(types.InlineKeyboardButton("🔄 Скасувати відгук", callback_data=f"unapply_{vacancy.id}"))
    markup.add(types.InlineKeyboardButton("🔄 Повернутись до вибору джерела", callback_data="back_to_source"))

    bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- Повернення до вибору джерела ---
@bot.callback_query_handler(func=lambda call: call.data == "back_to_source")
def back_to_source(call):
    choose_source(call.message)


if __name__ == "__main__":
    bot.polling(none_stop=True)
"""@bot.message_handler(commands=["vacancies"])
def send_vacancies(message):
    vacancies = Vacancy.objects.order_by("-created_at")
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
"""