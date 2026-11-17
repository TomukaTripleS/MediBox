from django.conf import settings
from django.db import models


class Kit(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_kits")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="shared_kits")
