from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rolepermissions.roles import assign_role, get_user_roles
from core.presentation.serializers.user_serializers import UserProfileSerializer
from core.presentation.permissions import HasPermissionFromToken, IsAdmin

User = get_user_model()


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [HasPermissionFromToken("view_users")]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [HasPermissionFromToken("view_users")]
        elif self.action in ["create"]:
            permission_classes = [HasPermissionFromToken("create_users")]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [HasPermissionFromToken("edit_users")]
        elif self.action in ["destroy"]:
            permission_classes = [HasPermissionFromToken("delete_users")]
        else:
            permission_classes = [HasPermissionFromToken("view_users")]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get("role")

        if not role:
            return Response(
                {"error": "Role is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        valid_roles = ["admin", "editor", "viewer"]
        if role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Must be one of {valid_roles}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assign_role(user, role)

        return Response({"success": f"Role '{role}' assigned to user {user.email}"})

    @action(detail=True, methods=["get"])
    def user_permissions(self, request, pk=None):
        user = self.get_object()
        roles = get_user_roles(user)

        permissions = {}
        if roles:
            role = roles[0]
            available_permissions = role.available_permissions
            for permission in available_permissions:
                permissions[permission] = True

        return Response(
            {
                "user": user.email,
                "roles": [role.get_name() for role in roles],
                "permissions": permissions,
            }
        )
