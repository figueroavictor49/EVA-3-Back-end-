from django.db import models
from django.contrib.auth.models import User


class Producto(models.Model):
    """
    Modelo representativo de los productos en bodega.
    Almacena información básica, stock disponible y fecha de actualización.
    """
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre del producto",
        help_text="Nombre descriptivo único del producto."
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
        help_text="Detalles o especificaciones adicionales del producto."
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock disponible",
        help_text="Cantidad actual de unidades disponibles en bodega."
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio unitario",
        help_text="Precio de venta unitario en CLP."
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"


class MovimientoInventario(models.Model):
    """
    Modelo de auditoría histórica para registrar cada intento o transacción de despacho,
    almacenando el estado resultante ('Aceptado', 'Rechazado', 'Inválido') y su motivo,
    preservando el comportamiento evaluado en Ev1.
    """
    ESTADO_ACEPTADO = 'Aceptado'
    ESTADO_RECHAZADO = 'Rechazado'
    ESTADO_INVALIDO = 'Inválido'

    ESTADOS_CHOICES = [
        (ESTADO_ACEPTADO, 'Aceptado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
        (ESTADO_INVALIDO, 'Inválido'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos',
        verbose_name="Producto asociado"
    )
    cantidad_solicitada = models.IntegerField(
        verbose_name="Cantidad solicitada",
        help_text="Número de unidades pedidas en la transacción."
    )
    stock_previo = models.IntegerField(
        verbose_name="Stock previo",
        help_text="Stock en bodega antes de evaluar la transacción."
    )
    stock_resultante = models.IntegerField(
        verbose_name="Stock resultante",
        help_text="Stock en bodega después de procesar la solicitud."
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        verbose_name="Estado de la transacción"
    )
    motivo = models.TextField(
        verbose_name="Motivo de la resolución",
        help_text="Justificación detallada de la aprobación o motivo del rechazo."
    )
    usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='movimientos',
        verbose_name="Usuario responsable"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha y hora de registro"
    )

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"[{self.estado}] {self.producto.nombre} - Cantidad: {self.cantidad_solicitada}"
