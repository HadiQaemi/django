from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.presentation.views.token_views import CustomTokenObtainPairView
from core.presentation.viewsets.auth_viewsets import (
    RegisterView,
    UserProfileView,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),
]
