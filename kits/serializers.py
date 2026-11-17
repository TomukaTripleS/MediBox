from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import Kit


class KitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kit
        fields = ["id", "name", "owner", "members"]
        read_only_fields = ["id", "owner"]

    def validate_members(self, value):
        if self.instance and self.instance.owner_id != self.context["request"].user.id:
            raise PermissionDenied("Лише власник може змінювати учасників.")
        return value
