"""
Servicios de lógica de negocio del sistema de inventario y despachos.
Preserva y extiende las 4 reglas de negocio de Ev1 garantizando consistencia transaccional (ACID).
"""
from django.db import transaction
from .models import Producto, MovimientoInventario


def decidir_salida_inventario(producto: str, stock_actual: int, cantidad_solicitada: int) -> tuple[str, str]:
    """
    Función pura que evalúa las 4 reglas de negocio para el despacho de inventario (proveniente de Ev1).
    Retorna una tupla: (estado, motivo)

    Reglas de negocio:
    1. Inválido: cantidad_solicitada <= 0 o stock_actual < 0
    2. Rechazado: cantidad_solicitada > 50 (límite superior de despacho)
    3. Rechazado: cantidad_solicitada > stock_actual (stock insuficiente)
    4. Aceptado: cantidad_solicitada <= stock_actual (aprobado y listo para despacho)
    """
    if cantidad_solicitada <= 0 or stock_actual < 0:
        return (
            MovimientoInventario.ESTADO_INVALIDO,
            "Error: La cantidad solicitada o el stock no pueden ser menores o iguales a cero."
        )
    elif cantidad_solicitada > 50:
        return (
            MovimientoInventario.ESTADO_RECHAZADO,
            "Excede el límite máximo de despacho permitido por transacción (Máx 50 unidades)."
        )
    elif cantidad_solicitada > stock_actual:
        return (
            MovimientoInventario.ESTADO_RECHAZADO,
            f"Stock insuficiente en bodega. Disponible: {stock_actual} unidades."
        )
    elif cantidad_solicitada <= stock_actual:
        return (
            MovimientoInventario.ESTADO_ACEPTADO,
            "Solicitud aprobada y lista para despacho."
        )
    else:
        return (
            MovimientoInventario.ESTADO_INVALIDO,
            "Error desconocido en los datos ingresados."
        )


def procesar_despacho(producto_id: int, cantidad_solicitada: int, usuario=None) -> MovimientoInventario:
    """
    Ejecuta el flujo completo de despacho de manera atómica con bloqueo a nivel de fila (select_for_update),
    previniendo condiciones de carrera (race conditions) en accesos concurrentes.
    
    Actualiza el stock si es aceptado y persiste el registro en el historial de movimientos.
    """
    with transaction.atomic():
        # Bloqueo pesimista para evitar que dos peticiones simultáneas descuenten más del stock real
        producto = Producto.objects.select_for_update().get(id=producto_id)
        stock_previo = producto.stock

        estado, motivo = decidir_salida_inventario(
            producto=producto.nombre,
            stock_actual=stock_previo,
            cantidad_solicitada=cantidad_solicitada
        )

        if estado == MovimientoInventario.ESTADO_ACEPTADO:
            producto.stock -= cantidad_solicitada
            producto.save(update_fields=['stock', 'actualizado_en'])
            stock_resultante = producto.stock
        else:
            stock_resultante = stock_previo

        movimiento = MovimientoInventario.objects.create(
            producto=producto,
            cantidad_solicitada=cantidad_solicitada,
            stock_previo=stock_previo,
            stock_resultante=stock_resultante,
            estado=estado,
            motivo=motivo,
            usuario=usuario
        )

        return movimiento
