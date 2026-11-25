from rest_framework import serializers

from .models import Medicine


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ["id", "name", "form", "unit"]

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", ""))
        form = attrs.get("form", getattr(self.instance, "form", ""))
        same = Medicine.objects.filter(kit=self.context["kit"], search_name=name.lower(), form=form)
        if self.instance:
            same = same.exclude(pk=self.instance.pk)
        if same.exists():
            raise serializers.ValidationError("Такий препарат уже є в цій аптечці.")
        return attrs
