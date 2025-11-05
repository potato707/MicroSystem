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
    path('hr/', include('hr_management.urls')),  # <--- include HR app routes
    path('pos/', include('pos_management.urls')),  # <--- POS Management Module
    path('api/', include('hr_management.tenant_urls')),  # <--- Tenant management API
    
    # Authentication endpoints
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="auth_login"),  # Alias for frontend
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # schema in raw OpenAPI json
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # ReDoc UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

