from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Simplified Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="REBORN API",
        default_version="v1",
        description="API for the REBORN research data platform",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API versions
    path(
        "api/v1/", include(("core.presentation.api.v1.urls", "api_v1"), namespace="v1")
    ),
    # Simplified API documentation paths
    path(
        "api/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

# Debug toolbar, static files, etc.
if settings.DEBUG:
    # Add debug toolbar URLs
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

    # Add static/media serving
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
