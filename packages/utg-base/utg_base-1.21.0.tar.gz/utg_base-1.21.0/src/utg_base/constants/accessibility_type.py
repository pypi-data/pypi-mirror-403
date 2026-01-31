from django.db import models


class AccessibilityType(models.TextChoices):
    ADMIN = "admin", "Админ"
    COMMON = "common", "Общая"
    METROLOG = "metrolog", "Метрология"
    DISPATCHER = "dispatcher", "Диспетчерский учет"
