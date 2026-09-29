"""
Permisos personalizados y diferenciados para la API REST (Rúbrica 3.1.2).
Establece niveles de acceso para usuarios anónimos, usuarios autenticados y administradores/staff.
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso diferenciado:
    - Métodos seguros (GET, HEAD, OPTIONS): Permitidos a cualquier usuario autenticado o lectura pública.
    - Métodos de modificación (POST, PUT, PATCH, DELETE): Exclusivos para usuarios con privilegios de Staff o Administrador.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAuthenticatedOrReadOnlyCustom(permissions.BasePermission):
    """
    Permite lectura a usuarios anónimos y creación/edición a cualquier usuario autenticado.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)


class SoloAdministradores(permissions.BasePermission):
    """
    Permiso estricto para operaciones críticas que sólo puede ejecutar un superusuario o staff.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))
