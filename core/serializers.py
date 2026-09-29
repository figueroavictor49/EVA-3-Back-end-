"""
Serializadores de Django REST Framework (Rúbrica 3.1.1, 3.1.3 y 3.1.4).
Transforman modelos y datos en representaciones JSON válidas y consistentes,
con validaciones explícitas de tipos y reglas de dominio.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Producto, MovimientoInventario


class UserSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para usuarios del sistema.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active', 'date_joined')
        read_only_fields = fields


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador para registrar nuevos usuarios con almacenamiento seguro de contraseñas (hashing).
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=6,
        help_text="Contraseña segura (mínimo 6 caracteres)."
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_staff')
        extra_kwargs = {
            'email': {'required': False},
            'is_staff': {'required': False, 'default': False}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            is_staff=validated_data.get('is_staff', False)
        )
        return user


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializador CRUD para el modelo Producto con validaciones de negocio.
    """
    class Meta:
        model = Producto
        fields = (
            'id',
            'nombre',
            'descripcion',
            'stock',
            'precio',
            'creado_en',
            'actualizado_en',
        )
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser un valor negativo.")
        return value

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value

    def validate_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre del producto no puede estar vacío.")
        return value.strip()


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de auditoría de movimientos de inventario.
    Incluye detalles legibles del producto y del usuario responsable.
    """
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username', default=None)

    class Meta:
        model = MovimientoInventario
        fields = (
            'id',
            'producto',
            'producto_nombre',
            'cantidad_solicitada',
            'stock_previo',
            'stock_resultante',
            'estado',
            'motivo',
            'usuario',
            'usuario_nombre',
            'fecha_registro',
        )
        read_only_fields = (
            'id',
            'producto_nombre',
            'stock_previo',
            'stock_resultante',
            'estado',
            'motivo',
            'usuario_nombre',
            'fecha_registro',
        )


class SolicitudDespachoSerializer(serializers.Serializer):
    """
    Serializador de entrada para solicitar salidas de inventario (Despachos).
    """
    producto_id = serializers.IntegerField(
        required=True,
        help_text="ID numérico del producto a despachar."
    )
    cantidad_solicitada = serializers.IntegerField(
        required=True,
        help_text="Cantidad de unidades a retirar de bodega."
    )

    def validate_producto_id(self, value):
        if not Producto.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"No existe ningún producto con el ID {value}.")
        return value


class ResultadoDespachoSerializer(serializers.Serializer):
    """
    Serializador de salida consistente para el resultado del despacho de inventario.
    """
    exito = serializers.BooleanField()
    estado = serializers.CharField()
    motivo = serializers.CharField()
    producto_id = serializers.IntegerField()
    producto_nombre = serializers.CharField()
    cantidad_solicitada = serializers.IntegerField()
    stock_previo = serializers.IntegerField()
    stock_resultante = serializers.IntegerField()
    movimiento_id = serializers.IntegerField()
    fecha_registro = serializers.DateTimeField()
