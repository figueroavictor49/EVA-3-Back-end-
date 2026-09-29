"""
Rutas de la aplicación Core y endpoints de la API REST (Rúbricas 3.1.1 y 3.1.4).
Utiliza routers automáticos de DRF para ViewSets y vistas explícitas para autenticación y despacho.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    ProductoViewSet,
    MovimientoInventarioViewSet,
    DespachoAPIView,
    RegistroUsuarioAPIView,
    PerfilUsuarioAPIView,
)

# Router automático según la documentación oficial de DRF
router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'movimientos', MovimientoInventarioViewSet, basename='movimiento')

urlpatterns = [
    # Endpoints de autenticación JWT y gestión de usuarios
    path('auth/registro/', RegistroUsuarioAPIView.as_view(), name='auth-registro'),
    path('auth/perfil/', PerfilUsuarioAPIView.as_view(), name='auth-perfil'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Endpoint transaccional de despacho de inventario
    path('despachos/', DespachoAPIView.as_view(), name='despacho-solicitud'),

    # Recursos RESTful gestionados por el router
    path('', include(router.urls)),
]
