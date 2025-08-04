from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    email        = models.EmailField("Email", max_length=254, unique=True)
    phone_number = models.CharField("Телефон", max_length=20, blank=True)

    # Переоприділяємо M2M, щоб не було двох user_set
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
