from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientTypeViewSet, ClientViewSet, ProductViewSet,
    DistributionViewSet,
    POSDashboardStatsView
)

router = DefaultRouter()
router.register(r'client-types', ClientTypeViewSet, basename='client-type')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'distributions', DistributionViewSet, basename='distribution')

urlpatterns = [
    # Dashboard statistics
    path('dashboard/stats/', POSDashboardStatsView.as_view(), name='pos-dashboard-stats'),
    
    # Router URLs
    path('', include(router.urls)),
]
