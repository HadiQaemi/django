from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def get_user_from_token(token):
    try:
        user_id = token.payload.get("user_id")
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return None
