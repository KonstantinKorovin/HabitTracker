from datetime import date, datetime

import requests
from celery import shared_task

from config.settings import TELEGRAM_BOT_TOKEN

from .models import Habit

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


@shared_task
def schedule_all_habits():
    today = date.today()

    habits_to_check = Habit.objects.filter(is_pleasant_habit=True)

    for habit in habits_to_check:
        is_due_today = False
        last_sent = habit.last_sent_date

        if last_sent is None:
            is_due_today = True

        else:
            days_since_last_sent = (today - last_sent).days

            if days_since_last_sent >= habit.periodicity:
                is_due_today = True

        if is_due_today:
            reminder_time = datetime.combine(today, habit.period)

            if reminder_time > datetime.now():
                send_habit_reminder.apply_async(
                    args=(habit.id,),
                    eta=reminder_time,
                )


@shared_task
def send_habit_reminder(habit_id):
    try:
        habit = Habit.objects.get(pk=habit_id)
        user = habit.user

        if not user.tg_chat_id:
            return

        message = (
            f"НАПОМИНАНИЕ О ПРИВЫЧКЕ: {habit.action}\n\n"
            f"МЕСТО: {habit.place}\n"
            f"ВРЕМЯ: {habit.period.strftime("%H:%M")}"
        )

        payload = {"chat_id": user.tg_chat_id, "text": message, "parse_mode": "HTML"}

        response = requests.post(url=TELEGRAM_URL, data=payload)

        habit.last_sent_date = date.today()
        habit.save(update_fields=["last_sent_date"])

        if response.status_code != 200:
            print(f"Ошибка отправки Telegram для {habit_id}: {response.text}")

    except Habit.DoesNotExist:
        pass
    except Exception as e:
        print(f"Ошибка при отправке напоминания ID {habit_id}: {e}")
