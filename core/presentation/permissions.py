from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication


class HasRoleFromToken(permissions.BasePermission):
    def __init__(self, required_role):
        self.required_role = required_role

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        jwt_auth = JWTAuthentication()
        validated_token = None

        try:
            header = jwt_auth.get_header(request)
            if header is None:
                return False

            raw_token = jwt_auth.get_raw_token(header)
            if raw_token is None:
                return False

            validated_token = jwt_auth.get_validated_token(raw_token)
        except Exception:
            return False

        roles = validated_token.get("roles", [])
        return self.required_role in roles


class HasPermissionFromToken(permissions.BasePermission):
    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        jwt_auth = JWTAuthentication()
        validated_token = None

        try:
            header = jwt_auth.get_header(request)
            if header is None:
                return False

            raw_token = jwt_auth.get_raw_token(header)
            if raw_token is None:
                return False

            validated_token = jwt_auth.get_validated_token(raw_token)
        except Exception:
            return False

        permissions = validated_token.get("permissions", {})
        return permissions.get(self.required_permission, False)


class IsAdmin(HasRoleFromToken):
    def __init__(self):
        super().__init__("admin")


class IsEditor(HasRoleFromToken):
    def __init__(self):
        super().__init__("editor")


class IsViewer(HasRoleFromToken):
    def __init__(self):
        super().__init__("viewer")


class CanViewPapers(permissions.BasePermission):
    def has_permission(self, request, view):
        # Always return True to allow access to everyone
        return True


class CanEditPapers(HasPermissionFromToken):
    def __init__(self):
        super().__init__("edit_papers")


class CanCreatePapers(HasPermissionFromToken):
    def __init__(self):
        super().__init__("create_papers")


class CanDeletePapers(HasPermissionFromToken):
    def __init__(self):
        super().__init__("delete_papers")
