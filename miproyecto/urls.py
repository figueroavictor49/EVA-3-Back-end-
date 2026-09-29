"""
miproyecto URL Configuration.
Organización completa y versionada de rutas para la API REST, Swagger y vistas web.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from core.views import resumen_html

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # API RESTful Versionada (v1)
    path('api/v1/', include('core.urls')),

    # Documentación interactiva de la API (OpenAPI 3.0 / Swagger / Redoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Vista web de resumen heredada y enriquecida desde Ev1
    path('resumen/', resumen_html, name='resumen'),

    # Redirección de la raíz hacia la documentación Swagger
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
]
