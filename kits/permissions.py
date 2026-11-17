from rest_framework.permissions import BasePermission


class KitPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.owner_id == request.user.id
        return True
