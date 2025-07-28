import logging
import json
from django.utils.deprecation import MiddlewareMixin
from rolepermissions.checkers import get_user_roles

logger = logging.getLogger("audit")


class RoleBasedAuditMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log for authenticated users
        if hasattr(request, "user") and request.user.is_authenticated:
            # Get user role
            role = get_user_roles(request.user)
            role_name = role.get_name() if role else "no_role"

            # Log based on method and status code
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                log_data = {
                    "user_id": request.user.id,
                    "user_email": request.user.email,
                    "role": role_name,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                }

                # Try to get request body for POST/PUT/PATCH
                if request.method in ["POST", "PUT", "PATCH"] and hasattr(
                    request, "body"
                ):
                    try:
                        # Don't log sensitive data like passwords
                        body = json.loads(request.body)
                        if "password" in body:
                            body["password"] = "********"
                        log_data["request_body"] = body
                    except:
                        pass

                logger.info(f"Audit: {json.dumps(log_data)}")

        return response
