from django.contrib import admin
from .models import Producto, MovimientoInventario


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'stock', 'precio', 'actualizado_en')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('actualizado_en',)
    ordering = ('nombre',)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_registro', 'producto', 'cantidad_solicitada', 'stock_previo', 'stock_resultante', 'estado', 'usuario')
    search_fields = ('producto__nombre', 'motivo', 'usuario__username')
    list_filter = ('estado', 'fecha_registro', 'producto')
    ordering = ('-fecha_registro',)
    readonly_fields = ('fecha_registro', 'stock_previo', 'stock_resultante', 'estado', 'motivo')
