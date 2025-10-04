from django.db import models
from django.utils import timezone


class Banner(models.Model):
    """Банер для головної сторінки"""
    title = models.CharField("Назва", max_length=255, blank=True)
    image = models.ImageField("Зображення", upload_to='banners/')
    link = models.URLField("Посилання", blank=True, help_text="Куди веде клік по банеру")
    position = models.PositiveIntegerField("Позиція", default=0, help_text="Чим менше - тим вище")
    is_active = models.BooleanField("Активний", default=True, db_index=True)
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        db_table = 'manager_banners'
        ordering = ['position', '-created_at']
        verbose_name = 'Банер'
        verbose_name_plural = 'Банери'

    def __str__(self):
        return f"{self.title or 'Банер'} (#{self.position})"
