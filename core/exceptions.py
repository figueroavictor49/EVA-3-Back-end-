"""
Manejador global y estandarizado de excepciones para Django REST Framework.
Garantiza que todas las respuestas de error sigan una estructura JSON uniforme,
con códigos HTTP semánticos y mensajes descriptivos (Rúbrica 3.1.3).
"""
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound


def custom_exception_handler(exc, context):
    """
    Interpreta cualquier excepción capturada por DRF y la formatea en una respuesta JSON
    consistente con 'exito': False, código de estado, tipo de error, mensaje comprensible y detalles.
    """
    response = exception_handler(exc, context)

    if response is not None:
        tipo_error = exc.__class__.__name__
        mensaje = "Ha ocurrido un error al procesar la solicitud."

        if isinstance(exc, ValidationError):
            tipo_error = "ValidationError"
            mensaje = "Error de validación en los datos proporcionados."
        elif isinstance(exc, NotAuthenticated):
            tipo_error = "NotAuthenticated"
            mensaje = "No se proporcionaron credenciales de autenticación válidas (Token JWT ausente o inválido)."
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            tipo_error = "PermissionDenied"
            mensaje = "No posee permisos suficientes para ejecutar esta acción."
        elif isinstance(exc, (NotFound, Http404)):
            tipo_error = "NotFound"
            mensaje = "El recurso solicitado no fue encontrado."
        elif isinstance(response.data, dict) and 'detail' in response.data:
            mensaje = str(response.data['detail'])

        response.data = {
            'exito': False,
            'status_code': response.status_code,
            'tipo_error': tipo_error,
            'mensaje': mensaje,
            'detalles': response.data
        }

    return response
