from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from hr_management.authentication import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('s/hr/', include('hr_management.urls')),  # <--- include HR app routes
    path('s/pos/', include('pos_management.urls')),  # <--- POS Management Module
    path('s/products/', include('product_management.urls')),  # <--- NEW: Advanced Product Management (separated from POS)
    path('s/api/', include('hr_management.tenant_urls')),  # <--- Tenant management API

    # Authentication endpoints
    path("s/api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("s/api/auth/login/", CustomTokenObtainPairView.as_view(), name="auth_login"),  # Alias for frontend
    path("s/api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # schema in raw OpenAPI json
    path("s/api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("s/api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # ReDoc UI
    path("s/api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

