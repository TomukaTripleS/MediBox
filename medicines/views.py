import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from kits.models import Kit

from .models import Medicine
from .serializers import MedicineSerializer

logger = logging.getLogger(__name__)

KIT_ID = OpenApiParameter("kit_pk", int, OpenApiParameter.PATH)
SEARCH = OpenApiParameter("search", str, description="Частина назви препарату")


@extend_schema_view(
    list=extend_schema(parameters=[KIT_ID, SEARCH]),
    create=extend_schema(parameters=[KIT_ID]),
    retrieve=extend_schema(parameters=[KIT_ID]),
    update=extend_schema(parameters=[KIT_ID]),
    partial_update=extend_schema(parameters=[KIT_ID]),
    destroy=extend_schema(parameters=[KIT_ID]),
)
class MedicineViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]

    def get_kit(self):
        user = self.request.user
        kits = Kit.objects.filter(Q(owner=user) | Q(members=user)).distinct()
        return get_object_or_404(kits, pk=self.kwargs["kit_pk"])

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Medicine.objects.none()
        medicines = Medicine.objects.filter(kit=self.get_kit())
        search = self.request.query_params.get("search", "").strip()
        if search:
            medicines = medicines.filter(search_name__contains=search.lower())
        return medicines

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            context["kit"] = self.get_kit()
        return context

    def perform_create(self, serializer):
        medicine = serializer.save(kit=self.get_kit())
        logger.info("Medicine created: medicine_id=%s user_id=%s", medicine.pk, self.request.user.pk)

    def perform_update(self, serializer):
        medicine = serializer.save()
        logger.info("Medicine updated: medicine_id=%s user_id=%s", medicine.pk, self.request.user.pk)

    def perform_destroy(self, instance):
        medicine_id = instance.pk
        instance.delete()
        logger.info("Medicine deleted: medicine_id=%s user_id=%s", medicine_id, self.request.user.pk)
