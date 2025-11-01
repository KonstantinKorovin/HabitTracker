from datetime import timedelta

from django.conf import settings
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    place = models.CharField(verbose_name="Место выполнения привычки")
    period = models.TimeField(verbose_name="Время когда необходимо выполнять привычку")
    action = models.CharField(
        verbose_name="Действие которое представляет из себя привычка",
    )
    is_pleasant_habit = models.BooleanField(
        verbose_name="Признак приятной привычки",
        default=True,
    )
    related_habit = models.ForeignKey(
        to="self",
        on_delete=models.SET_NULL,
        related_name="antecedent_habits",
        verbose_name="Связанная привычка",
        blank=True,
        null=True,
    )
    periodicity = models.IntegerField(
        verbose_name="Периодичность выполнения привычки",
        default=1,
    )
    reward = models.CharField(verbose_name="Награда за выполнение полезной привычки")
    time_to_complete = models.DurationField(
        verbose_name="Время на выполнение привычки",
        default=timedelta(seconds=120),
    )
    is_published = models.BooleanField(
        verbose_name="Статус публикации привычки",
        default=False,
    )

    def __str__(self):
        return f"я буду {self.action} в {self.period.strftime("%H:%M")} в {self.place}"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
