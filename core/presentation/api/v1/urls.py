from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.presentation.viewsets.auto_complete_viewsets import AutoCompleteViewSet
from core.presentation.viewsets.nlsql_viewsets import NLSQLViewSet
from core.presentation.viewsets.paper_viewsets import PaperViewSet
from core.presentation.viewsets.insight_viewsets import InsightViewSet

router = DefaultRouter()
router.register(r"articles", PaperViewSet, basename="paper")
router.register(r"auto-complete", AutoCompleteViewSet, basename="auto-complete")
router.register(r"insight", InsightViewSet, basename="insight")
router.register(r'nlsql', NLSQLViewSet, basename='nlsql')

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
]
