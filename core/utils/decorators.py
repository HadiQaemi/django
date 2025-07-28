from functools import wraps
from django.http import HttpResponseForbidden
from rest_framework_simplejwt.authentication import JWTAuthentication


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")

            jwt_auth = JWTAuthentication()
            validated_token = None

            try:
                header = jwt_auth.get_header(request)
                if header is None:
                    return HttpResponseForbidden("Authentication required")

                raw_token = jwt_auth.get_raw_token(header)
                if raw_token is None:
                    return HttpResponseForbidden("Authentication required")

                validated_token = jwt_auth.get_validated_token(raw_token)
            except Exception:
                return HttpResponseForbidden("Invalid authentication token")

            roles = validated_token.get("roles", [])
            if role not in roles:
                return HttpResponseForbidden(f"Role '{role}' required")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")

            jwt_auth = JWTAuthentication()
            validated_token = None

            try:
                header = jwt_auth.get_header(request)
                if header is None:
                    return HttpResponseForbidden("Authentication required")

                raw_token = jwt_auth.get_raw_token(header)
                if raw_token is None:
                    return HttpResponseForbidden("Authentication required")

                validated_token = jwt_auth.get_validated_token(raw_token)
            except Exception:
                return HttpResponseForbidden("Invalid authentication token")

            permissions = validated_token.get("permissions", {})
            if not permissions.get(permission, False):
                return HttpResponseForbidden(f"Permission '{permission}' required")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def view_papers_allowed(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view
