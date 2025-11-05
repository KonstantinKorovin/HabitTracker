from django.contrib.auth import get_user_model
from rest_framework import status, test

from users.serializers import CustomUserSerializer

User = get_user_model()


class CustomUserTests(test.APITestCase):
    def test_register_success(self):
        """Успешная регистрация"""
        data = {
            "username": "testuser",
            "email": "test.user@email.ru",
            "password": "test1password2",
            "phone_number": "89999999898",
        }
        response = self.client.post("/users/register/", data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test.user@email.ru").exists())

    def test_register_duplicate_email(self):
        """Дубликат email"""
        User.objects.create_user(
            username="first",
            email="alex1@email.ru",
            phone_number="88887776655",
            password="pass1234",
        )
        data = {
            "username": "second",
            "email": "alex1@email.ru",
            "password": "test1password2",
            "phone_number": "89999999898",
        }
        response = self.client.post("/users/register/", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_serializer_create(self):
        """Проверка метода сериализатора create"""
        data = {
            "username": "testuser",
            "email": "test.user@email.ru",
            "password": "test1password2",
            "phone_number": "89999999898",
        }
        serializer = CustomUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(user.check_password("test1password2"))
