from datetime import timedelta

from rest_framework import serializers, validators

from habits.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"

        extra_kwargs = {"user": {"read_only": True}}

    def validate(self, data):
        related_habit = data.get("related_habit")
        reward = data.get("reward")

        has_reward = bool(reward and reward.strip())
        has_related_habit = bool(related_habit)

        if has_reward and has_related_habit:
            raise validators.ValidationError(
                {
                    "non_field_errors": "Нельзя одновременно указывать связанную привычку и вознаграждение."
                    "\nВыберите что-то одно."
                }
            )

        is_pleasant = data.get("is_pleasant_habit")

        if is_pleasant is True:
            if has_reward:
                raise serializers.ValidationError(
                    {
                        "reward": "Приятная привычка не может иметь отдельное вознаграждение."
                    }
                )
            if has_related_habit:
                raise serializers.ValidationError(
                    {
                        "related_habit": "Приятная привычка не может иметь связанную привычку."
                    }
                )

        if related_habit is not None:
            if not related_habit.is_pleasant_habit:
                raise validators.ValidationError(
                    {
                        "В связанные привычки могут попадать только привычки с признаком 'приятная привычка'."
                    }
                )

        if is_pleasant is False:
            if not has_reward and not related_habit:
                raise serializers.ValidationError(
                    "Полезная привычка должна иметь либо вознаграждение, либо связанную приятную привычку."
                )

        return data

    def validate_time_to_complete(self, value: timedelta):
        max_time = timedelta(seconds=120)

        if value > max_time:
            raise serializers.ValidationError(
                "Время на выполнение привычки не должно превышать 120 секунд (2 минуты)."
            )
        return value

    def validate_periodicity(self, value):
        if value < 1 or value > 7:
            raise serializers.ValidationError(
                "Периодичность выполнения привычки должна быть не реже, чем 1 раз в 7 дней (диапазон от 1 до 7)."
            )
        return value
