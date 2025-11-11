from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientTypeViewSet, ClientViewSet, ProductViewSet as OldProductViewSet,
    DistributionViewSet, ClientInventoryViewSet,
    POSDashboardStatsView
)
from .product_views import (
    ProductCategoryViewSet,
    ProductUnitViewSet,
    CategoryUnitViewSet,
    ProductViewSet as NewProductViewSet,
    ProductUnitStockViewSet,
)

router = DefaultRouter()
router.register(r'client-types', ClientTypeViewSet, basename='client-type')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'products-old', OldProductViewSet, basename='product-old')
router.register(r'distributions', DistributionViewSet, basename='distribution')
router.register(r'inventory', ClientInventoryViewSet, basename='inventory')

# New Product Management
router.register(r'product-categories', ProductCategoryViewSet, basename='product-category')
router.register(r'product-units', ProductUnitViewSet, basename='product-unit')
router.register(r'category-units', CategoryUnitViewSet, basename='category-unit')
router.register(r'products', NewProductViewSet, basename='product')
router.register(r'product-stocks', ProductUnitStockViewSet, basename='product-stock')

urlpatterns = [
    # Dashboard statistics
    path('dashboard/stats/', POSDashboardStatsView.as_view(), name='pos-dashboard-stats'),
    
    # Router URLs
    path('', include(router.urls)),
]

