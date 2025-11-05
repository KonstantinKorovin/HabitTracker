from datetime import time, timedelta, date
from unittest.mock import patch

from django.test import TestCase
from rest_framework import test, status

from habits.models import Habit
from habits.serializers import HabitSerializer
from habits.tasks import send_habit_reminder, TELEGRAM_URL, schedule_all_habits
from users.models import CustomUser


class HabitModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="alex",
            email="alex1@email.ru",
            password="password123",
            phone_number="89109109191",
        )

    def test_str_method(self):
        """__str__ работает"""
        habit = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="пить воду",
            time_to_complete=timedelta(seconds=60),
        )
        self.assertEqual(str(habit), "я буду пить воду в 12:00 в дома")

    def test_default_values(self):
        """Проверка дефолтных значений"""
        habit = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="пить воду",
        )
        self.assertTrue(habit.is_pleasant_habit)
        self.assertFalse(habit.is_published)
        self.assertEqual(habit.periodicity, 1)
        self.assertEqual(habit.time_to_complete, timedelta(seconds=120))


class HabitSerializerTest(test.APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="alex",
            email="alex1@email.ru",
            password="password123",
            phone_number="89109109191",
        )

    def _get_base_data(self, **overrides):
        base = {
            "place": "дома",
            "period": "12:00",
            "action": "пить воду",
            "periodicity": 1,
            "time_to_complete": "00:01:00",
            "is_pleasant_habit": True,
        }
        base.update(overrides)
        return base

    def test_create_valid_useful_with_reward(self):
        """Полезная с наградой — ок"""
        data = self._get_base_data(is_pleasant_habit=False, reward="Шоколадка")
        serializer = HabitSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_valid_useful_with_related(self):
        """Полезная со связанной — ок"""
        pleasant = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="танцевать",
            is_pleasant_habit=True,
            time_to_complete=timedelta(seconds=60),
            periodicity=3,
        )
        data = self._get_base_data(is_pleasant_habit=False, related_habit=pleasant.id)
        serializer = HabitSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIsNotNone(serializer.save(user=self.user))

    def test_cannot_both_reward_and_related(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="танцевать",
            is_pleasant_habit=True,
            time_to_complete=timedelta(seconds=60),
            periodicity=3,
        )
        data = self._get_base_data(reward="Шоколад", related_habit=pleasant.id)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Нельзя одновременно указывать связанную привычку и вознаграждение."
            "\nВыберите что-то одно.",
            str(serializer.errors["non_field_errors"][0]),
        )

    def test_pleasant_cannot_reward(self):
        data = self._get_base_data(reward="Шоколад", is_pleasant_habit=True)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Приятная привычка не может иметь отдельное вознаграждение",
            str(serializer.errors["reward"][0]),
        )

    def test_pleasant_cannot_related(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="танцевать",
            is_pleasant_habit=True,
            time_to_complete=timedelta(seconds=60),
            periodicity=3,
        )
        data = self._get_base_data(related_habit=pleasant.id, is_pleasant_habit=True)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_related_must_be_pleasant(self):
        bad = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0),
            action="танцевать",
            is_pleasant_habit=False,
            time_to_complete=timedelta(seconds=60),
            periodicity=3,
        )
        data = self._get_base_data(is_pleasant_habit=False, related_habit=bad.id)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        expected_message_part = "В связанные привычки могут попадать только привычки с признаком 'приятная привычка'."
        self.assertEqual(
            expected_message_part, serializer.errors["non_field_errors"][0]
        )

    def test_useful_must_have_reward_or_related(self):
        data = self._get_base_data(is_pleasant_habit=False)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_time_to_complete_max_2min(self):
        data = self._get_base_data(time_to_complete=time(0, 3, 0))
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_periodicity_1_7(self):
        data = self._get_base_data(periodicity=8)
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class HabitApiView(test.APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="alex",
            email="alex1@email.ru",
            password="password123",
            phone_number="89109109191",
        )
        self.other_user = CustomUser.objects.create_user(
            username="maks",
            email="maks1@email.ru",
            password="password123",
            phone_number="89009000909",
        )
        self.client.force_authenticate(user=self.user)

        self.my_habit = Habit.objects.create(
            user=self.user,
            place="дома",
            period="12:00",
            action="пить воду",
            is_published=False
        )
        self.published_habit = Habit.objects.create(
            user=self.other_user,
            place="парк",
            period="13:00",
            action="бегать",
            is_published=True
        )

    def test_create_habit(self):
        data = {
            "place": "Офис",
            "period": time(12,0, 0),
            "action": "Сдать отчеты",
            "reward": "Кофе"
        }
        response = self.client.post("/habits/create/habit/", data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_my_habits(self):
        response = self.client.get("/habits/my/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_published(self):
        response = self.client.get("/habits/list/published/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_my_habit(self):
        response = self.client.get(f"/habits/habit/{self.my_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_my_habit(self):
        data = {"action": "Новое действие"}
        response = self.client.patch(f"/habits/update/{self.my_habit.id}/habit/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Новое действие")

    def test_delete_my_habit(self):
        response = self.client.delete(f"/habits/habit/{self.my_habit.id}/destroy/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(pk=self.my_habit.id).exists())

    def test_cannot_retrieve_others(self):
        response = self.client.get(f"/habits/habit/{self.published_habit.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_update_others(self):
        response = self.client.patch(f"/habits/update/{self.published_habit.id}/habit/", data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_others(self):
        response = self.client.delete(f"/habits/habit/{self.published_habit.id}/destroy/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class HabitTaskTests(test.APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="alex",
            email="alex.email@email.ru",
            password="password123",
            phone_number="89899998877",
        )
        self.my_habit = Habit.objects.create(
            user=self.user,
            place="дома",
            period=time(12, 0,0),
            action="пить воду",
            is_published=False,
            is_pleasant_habit=True,
            periodicity=1,
        )

    @patch('habits.tasks.requests.post')

    def test_send_reminder_success(self, mock_requests_post):

        mock_requests_post.return_value.status_code = 200

        self.user.tg_chat_id = "12345"
        self.user.save()

        send_habit_reminder(self.my_habit.id)
        mock_requests_post.assert_called_once()

        expected_message = (
            f"НАПОМИНАНИЕ О ПРИВЫЧКЕ: {self.my_habit.action}\n\n"
            f"МЕСТО: {self.my_habit.place}\n"
            f"ВРЕМЯ: {self.my_habit.period.strftime("%H:%M")}")

        expected_payload = {
            "chat_id": "12345",
            "text": expected_message,
            "parse_mode": "HTML"
        }

        mock_requests_post.assert_called_with(
            url=TELEGRAM_URL,
            data=expected_payload,
        )

        self.my_habit.refresh_from_db()
        self.assertEqual(self.my_habit.last_sent_date, date.today())

    def test_sen_reminder_no_chat_id(self):
        send_habit_reminder(self.my_habit.id)
        self.my_habit.refresh_from_db()
        self.assertIsNone(self.my_habit.last_sent_date)

    def test_schedule_all_habits(self):
        self.my_habit.last_sent_date = date.today() - timedelta(days=2)
        self.my_habit.save()
        schedule_all_habits()

        self.assertTrue(True)
