from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    username = models.CharField(
        "ПІБ",
        max_length=150,
        unique=False,
        help_text="Введіть ваше повне ім'я",
        validators=[],  # Прибираємо всі валідатори
        error_messages={
            'unique': "Користувач з таким іменем вже існує.",
        },
    )
    email        = models.EmailField("Email", max_length=254, unique=True)
    phone_number = models.CharField("Телефон", max_length=20, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        verbose_name="групи"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",
        blank=True,
        verbose_name="дозволи"
    )

    def __str__(self):
        return self.username
