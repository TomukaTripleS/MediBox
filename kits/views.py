import logging

from django.db.models import Q
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Kit
from .permissions import KitPermission
from .serializers import KitSerializer

logger = logging.getLogger(__name__)


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ValidationErrorSerializer(serializers.Serializer):
    name = serializers.ListField(child=serializers.CharField(), required=False)
    members = serializers.ListField(child=serializers.CharField(), required=False)
    non_field_errors = serializers.ListField(child=serializers.CharField(), required=False)


UNAUTHORIZED = OpenApiResponse(ErrorSerializer, description="Відсутній або недійсний access-токен.")
NOT_FOUND = OpenApiResponse(ErrorSerializer, description="Аптечка не існує або недоступна користувачу.")
FORBIDDEN = OpenApiResponse(ErrorSerializer, description="Дія доступна лише власнику аптечки.")
INVALID = OpenApiResponse(ValidationErrorSerializer, description="Некоректна назва або ID учасників.")
WRITE_EXAMPLE = OpenApiExample("Аптечка", value={"name": "Домашня аптечка", "members": []}, request_only=True)


@extend_schema_view(
    list=extend_schema(summary="Мої аптечки", description="Лише власні аптечки та аптечки, до яких вас додали. Параметрів запиту немає.", responses={200: KitSerializer(many=True), 401: UNAUTHORIZED}),
    retrieve=extend_schema(summary="Перегляд аптечки", responses={200: KitSerializer, 401: UNAUTHORIZED, 404: NOT_FOUND}),
    create=extend_schema(summary="Створення аптечки", description="Власником автоматично стає поточний користувач. members — ID існуючих користувачів (необов’язково).", examples=[WRITE_EXAMPLE], responses={201: KitSerializer, 400: INVALID, 401: UNAUTHORIZED}),
    update=extend_schema(summary="Заміна даних аптечки", description="name обов’язкове. Якщо members пропущено, склад зберігається. Учасник може змінювати назву; поле members може надсилати лише власник. Власник незмінний.", examples=[WRITE_EXAMPLE], responses={200: KitSerializer, 400: INVALID, 401: UNAUTHORIZED, 403: FORBIDDEN, 404: NOT_FOUND}),
    partial_update=extend_schema(summary="Часткове редагування аптечки", description="Передавайте лише змінені поля. Учасник може змінювати назву; поле members може надсилати лише власник. Власник незмінний.", examples=[OpenApiExample("Нова назва", value={"name": "Сімейна аптечка"}, request_only=True)], responses={200: KitSerializer, 400: INVALID, 401: UNAUTHORIZED, 403: FORBIDDEN, 404: NOT_FOUND}),
    destroy=extend_schema(summary="Видалення аптечки", description="Лише власник може видалити аптечку.", responses={204: None, 401: UNAUTHORIZED, 403: FORBIDDEN, 404: NOT_FOUND}),
)
class KitViewSet(viewsets.ModelViewSet):
    serializer_class = KitSerializer
    permission_classes = [IsAuthenticated, KitPermission]
    queryset = Kit.objects.all()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Kit.objects.none()
        return Kit.objects.filter(Q(owner=self.request.user) | Q(members=self.request.user)).distinct().order_by("id")

    def perform_create(self, serializer):
        kit = serializer.save(owner=self.request.user)
        logger.info("Kit created: kit_id=%s user_id=%s", kit.pk, self.request.user.pk)

    def perform_update(self, serializer):
        kit = serializer.save()
        logger.info("Kit updated: kit_id=%s user_id=%s", kit.pk, self.request.user.pk)

    def perform_destroy(self, instance):
        kit_id = instance.pk
        instance.delete()
        logger.info("Kit deleted: kit_id=%s user_id=%s", kit_id, self.request.user.pk)

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        logger.warning(
            "Kit request rejected: action=%s user_id=%s status=%s",
            self.action, self.request.user.pk, response.status_code,
        )
        return response
