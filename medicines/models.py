from django.db import models

from kits.models import Kit

FORMS = [
    ("tablet", "Таблетки"),
    ("capsule", "Капсули"),
    ("syrup", "Сироп"),
    ("drops", "Краплі"),
    ("ointment", "Мазь"),
    ("spray", "Спрей"),
    ("injection", "Ін’єкції"),
    ("powder", "Порошок"),
    ("other", "Інше"),
]
UNITS = [("pcs", "шт"), ("ml", "мл"), ("g", "г")]


class Medicine(models.Model):
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name="medicines")
    name = models.CharField(max_length=150)
    search_name = models.CharField(max_length=150, editable=False)
    form = models.CharField(max_length=20, choices=FORMS)
    unit = models.CharField(max_length=10, choices=UNITS)

    class Meta:
        ordering = ["search_name", "id"]

    def save(self, *args, **kwargs):
        self.search_name = self.name.lower()
        super().save(*args, **kwargs)
