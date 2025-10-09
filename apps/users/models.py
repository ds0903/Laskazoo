from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta

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
    
    # Поля для одноразового токену скидання паролю
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_created = models.DateTimeField(blank=True, null=True)
    password_reset_token_used = models.BooleanField(default=False)

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
    
    def is_token_valid(self, token):
        """Перевірка чи токен ще дійсний (не використаний і не застарілий)"""
        if not self.password_reset_token or self.password_reset_token_used:
            return False
        
        if self.password_reset_token != token:
            return False
        
        # Перевірка на 30 хвилин
        if self.password_reset_token_created:
            expiry_time = self.password_reset_token_created + timedelta(minutes=30)
            if timezone.now() > expiry_time:
                return False
        
        return True
    
    def mark_token_as_used(self):
        """Позначити токен як використаний"""
        self.password_reset_token_used = True
        self.save()
