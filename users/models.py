from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=254, verbose_name="E-mail пользователя", unique=True
    )
    phone_number = models.CharField(
        max_length=20, verbose_name="Номер телефона", unique=True, blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
    ]

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
