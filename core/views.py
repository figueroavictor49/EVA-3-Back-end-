"""
Vistas y ViewSets de Django REST Framework (Rúbricas 3.1.1, 3.1.2, 3.1.3 y 3.1.4).
Implementa operaciones RESTful completas, control de permisos diferenciados,
filtrado, búsqueda, paginación y documentación OpenAPI con drf-spectacular.
"""
from rest_framework import viewsets, status, permissions, generics, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Producto, MovimientoInventario
from .serializers import (
    ProductoSerializer,
    MovimientoInventarioSerializer,
    SolicitudDespachoSerializer,
    ResultadoDespachoSerializer,
    RegistroUsuarioSerializer,
    UserSerializer,
)
from .permissions import IsAdminOrReadOnly
from .services import procesar_despacho


class ProductoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para el catálogo de productos en inventario.
    - Lectura (GET): Abierta a clientes / usuarios autenticados.
    - Escritura (POST, PUT, PATCH, DELETE): Exclusiva para Staff / Administradores.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['stock']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['id', 'nombre', 'stock', 'precio', 'creado_en']
    ordering = ['nombre']

    @extend_schema(
        summary="Listar movimientos de un producto",
        description="Obtiene el historial de despachos asociados a un producto específico.",
        responses={200: MovimientoInventarioSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def movimientos(self, request, pk=None):
        producto = self.get_object()
        movimientos = producto.movimientos.all().order_by('-fecha_registro')
        page = self.paginate_queryset(movimientos)
        if page is not None:
            serializer = MovimientoInventarioSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MovimientoInventarioSerializer(movimientos, many=True)
        return Response(serializer.data)


class MovimientoInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint de sólo lectura para consultar la auditoría histórica de movimientos y despachos.
    Protegido: Requiere autenticación JWT.
    """
    queryset = MovimientoInventario.objects.select_related('producto', 'usuario').all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['estado', 'producto']
    search_fields = ['producto__nombre', 'motivo', 'usuario__username']
    ordering_fields = ['id', 'fecha_registro', 'cantidad_solicitada']
    ordering = ['-fecha_registro']

    @extend_schema(
        summary="Estadísticas de movimientos",
        description="Devuelve el conteo general de solicitudes agrupadas por estado (Aceptado, Rechazado, Inválido).",
        responses={200: OpenApiResponse(description="Resumen cuantitativo de transacciones")}
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        total = self.queryset.count()
        aceptados = self.queryset.filter(estado=MovimientoInventario.ESTADO_ACEPTADO).count()
        rechazados = self.queryset.filter(estado=MovimientoInventario.ESTADO_RECHAZADO).count()
        invalidos = self.queryset.filter(estado=MovimientoInventario.ESTADO_INVALIDO).count()

        return Response({
            'total_movimientos': total,
            'aceptados': aceptados,
            'rechazados': rechazados,
            'invalidos': invalidos,
        })


class DespachoAPIView(views.APIView):
    """
    Endpoint transaccional para procesar solicitudes de salida de inventario.
    Evalúa las 4 reglas de negocio de Ev1 y actualiza atómicamente el stock.
    Requiere autenticación JWT.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Solicitar despacho de inventario",
        description=(
            "Evalúa la solicitud de retiro de stock según las reglas de negocio:\n"
            "- Inválido: cantidad <= 0 o stock < 0 (Código 400)\n"
            "- Rechazado: cantidad > 50 (Código 200 con estado 'Rechazado')\n"
            "- Rechazado: cantidad > stock disponible (Código 200 con estado 'Rechazado')\n"
            "- Aceptado: cantidad <= stock disponible (Código 201 y descuenta stock)"
        ),
        request=SolicitudDespachoSerializer,
        responses={
            201: ResultadoDespachoSerializer,
            200: ResultadoDespachoSerializer,
            400: OpenApiResponse(description="Parámetros inválidos"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = SolicitudDespachoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        producto_id = serializer.validated_data['producto_id']
        cantidad_solicitada = serializer.validated_data['cantidad_solicitada']

        movimiento = procesar_despacho(
            producto_id=producto_id,
            cantidad_solicitada=cantidad_solicitada,
            usuario=request.user if request.user.is_authenticated else None
        )

        es_aceptado = movimiento.estado == MovimientoInventario.ESTADO_ACEPTADO
        es_invalido = movimiento.estado == MovimientoInventario.ESTADO_INVALIDO

        resultado = {
            'exito': es_aceptado,
            'estado': movimiento.estado,
            'motivo': movimiento.motivo,
            'producto_id': movimiento.producto.id,
            'producto_nombre': movimiento.producto.nombre,
            'cantidad_solicitada': movimiento.cantidad_solicitada,
            'stock_previo': movimiento.stock_previo,
            'stock_resultante': movimiento.stock_resultante,
            'movimiento_id': movimiento.id,
            'fecha_registro': movimiento.fecha_registro,
        }

        output_serializer = ResultadoDespachoSerializer(resultado)

        if es_invalido:
            return Response(output_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        elif es_aceptado:
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(output_serializer.data, status=status.HTTP_200_OK)


class RegistroUsuarioAPIView(generics.CreateAPIView):
    """
    Endpoint público para crear nuevas cuentas de usuario en el sistema.
    """
    queryset = User.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [permissions.AllowAny]


class PerfilUsuarioAPIView(views.APIView):
    """
    Endpoint para consultar el perfil del usuario autenticado actual.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Obtener perfil de usuario actual",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


def resumen_html(request):
    """
    Vista HTML de resumen heredada de Ev1, adaptada para leer dinámicamente desde la BD
    o desde datos.json como respaldo para total compatibilidad.
    """
    movimientos = MovimientoInventario.objects.select_related('producto').all().order_by('-fecha_registro')
    registros = []

    if movimientos.exists():
        for m in movimientos:
            registros.append({
                'producto': m.producto.nombre,
                'stock_actual': m.stock_resultante,
                'cantidad_solicitada': m.cantidad_solicitada,
                'estado': m.estado,
                'motivo': m.motivo,
            })
    else:
        # Respaldo desde datos.json para compatibilidad exacta con Ev1
        import json
        from pathlib import Path
        from django.conf import settings
        archivo_json = Path(settings.BASE_DIR) / "datos.json"
        if archivo_json.exists():
            try:
                with open(archivo_json, "r", encoding="utf-8") as f:
                    registros = json.load(f)
            except Exception:
                registros = []

    return render(request, "resumen.html", {"registros": registros})
