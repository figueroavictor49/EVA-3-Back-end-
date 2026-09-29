"""
Comando de gestión para inicializar la base de datos con usuarios y datos desde datos.json.
Facilita la evaluación inmediata del proyecto.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from core.models import Producto, MovimientoInventario


class Command(BaseCommand):
    help = "Carga usuarios iniciales y productos basados en datos.json e inventario de Ev1"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos iniciales..."))

        # 1. Crear Superusuario / Admin
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@inacap.cl',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created_admin:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Usuario 'admin' creado (password: admin123)."))
        else:
            self.stdout.write("Usuario 'admin' ya existía.")

        # 2. Crear Operador estándar
        operador_user, created_op = User.objects.get_or_create(
            username='operador',
            defaults={
                'email': 'operador@bodega.cl',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created_op:
            operador_user.set_password('operador123')
            operador_user.save()
            self.stdout.write(self.style.SUCCESS("Usuario 'operador' creado (password: operador123)."))
        else:
            self.stdout.write("Usuario 'operador' ya existía.")

        # 3. Crear productos base
        productos_base = [
            {"nombre": "arroz", "descripcion": "Arroz grano largo grado 1 (1kg)", "stock": 100, "precio": 1290.00},
            {"nombre": "fideos", "descripcion": "Fideos Spaghetti N° 5 (400g)", "stock": 80, "precio": 890.00},
            {"nombre": "aceite", "descripcion": "Aceite vegetal 100% puro (900ml)", "stock": 45, "precio": 2190.00},
            {"nombre": "azucar", "descripcion": "Azúcar blanca refinada (1kg)", "stock": 60, "precio": 1150.00},
            {"nombre": "leche", "descripcion": "Leche entera larga vida (1L)", "stock": 12, "precio": 1050.00},
        ]

        for p_data in productos_base:
            producto, created = Producto.objects.get_or_create(
                nombre=p_data["nombre"],
                defaults={
                    "descripcion": p_data["descripcion"],
                    "stock": p_data["stock"],
                    "precio": p_data["precio"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Producto '{producto.nombre}' creado."))

        # 4. Importar movimientos desde datos.json (si existe)
        json_path = Path(settings.BASE_DIR) / "datos.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    registros = json.load(f)
                    for r in registros:
                        nombre_prod = r.get("producto", "arroz").strip()
                        producto, _ = Producto.objects.get_or_create(
                            nombre=nombre_prod,
                            defaults={"stock": r.get("stock_actual", 100), "precio": 1290.00}
                        )

                        # Evitar duplicar registros iniciales idénticos
                        if not MovimientoInventario.objects.filter(
                            producto=producto,
                            cantidad_solicitada=r.get("cantidad_solicitada", 0),
                            estado=r.get("estado", "Aceptado")
                        ).exists():
                            MovimientoInventario.objects.create(
                                producto=producto,
                                cantidad_solicitada=r.get("cantidad_solicitada", 0),
                                stock_previo=r.get("stock_actual", 100),
                                stock_resultante=r.get("stock_actual", 100) - r.get("cantidad_solicitada", 0) if r.get("estado") == "Aceptado" else r.get("stock_actual", 100),
                                estado=r.get("estado", "Aceptado"),
                                motivo=r.get("motivo", "Carga inicial desde datos.json"),
                                usuario=operador_user
                            )
                            self.stdout.write(self.style.SUCCESS(f"Movimiento para '{nombre_prod}' importado desde datos.json."))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"No se pudo procesar datos.json: {e}"))

        self.stdout.write(self.style.SUCCESS("¡Carga inicial completada exitosamente!"))
