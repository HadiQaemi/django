from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.presentation.viewsets.auto_complete_viewsets import AutoCompleteViewSet
from core.presentation.viewsets.paper_viewsets import PaperViewSet
from core.presentation.viewsets.insight_viewsets import InsightViewSet
from core.presentation.viewsets.user_management_viewset import UserManagementViewSet

router = DefaultRouter()
router.register(r"articles", PaperViewSet, basename="paper")
# router.register(r"search", SearchViewSet, basename="search")
router.register(r"auto-complete", AutoCompleteViewSet, basename="auto-complete")
router.register(r"insight", InsightViewSet, basename="insight")
router.register(r"users", UserManagementViewSet, basename="users")

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Include authentication URLs
    path("auth/", include("core.presentation.api.v1.auth_urls")),
]
