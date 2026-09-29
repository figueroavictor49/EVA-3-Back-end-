"""
Conjunto exhaustivo de pruebas automatizadas (Rúbricas 3.1.1, 3.1.2, 3.1.3 y 3.1.4).
Verifica configuración de DRF, autenticación JWT, permisos diferenciados,
consistencia JSON, manejo de excepciones y las 4 reglas de negocio de Ev1.
"""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Producto, MovimientoInventario
from core.services import decidir_salida_inventario


class ConfiguracionDRFTests(APITestCase):
    """
    Rúbrica 3.1.1: Verifica configuración de DRF, routers, paginación,
    versionado y endpoints de esquema OpenAPI.
    """
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin_drf', password='password123', email='admin@test.cl')
        for i in range(15):
            Producto.objects.create(nombre=f"Producto {i+1}", stock=20 + i, precio=100.0 * (i + 1))

    def test_router_expone_rutas_correctas(self):
        url = reverse('producto-list')
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', respuesta['Content-Type'])

    def test_paginacion_configurada_y_metadatos_en_json(self):
        url = reverse('producto-list')
        respuesta = self.client.get(url, {'page': 1, 'page_size': 5})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        
        datos = respuesta.json()
        self.assertIn('count', datos)
        self.assertIn('total_pages', datos)
        self.assertIn('current_page', datos)
        self.assertIn('page_size', datos)
        self.assertIn('results', datos)
        self.assertEqual(datos['count'], 15)
        self.assertEqual(len(datos['results']), 5)
        self.assertEqual(datos['total_pages'], 3)

    def test_versionado_y_esquema_openapi(self):
        url_schema = reverse('schema')
        respuesta_schema = self.client.get(url_schema)
        self.assertEqual(respuesta_schema.status_code, status.HTTP_200_OK)

        url_swagger = reverse('swagger-ui')
        respuesta_swagger = self.client.get(url_swagger)
        self.assertEqual(respuesta_swagger.status_code, status.HTTP_200_OK)


class AutenticacionYPermisosTests(APITestCase):
    """
    Rúbrica 3.1.2: Verifica emisión y refresco de tokens JWT,
    protección de endpoints y permisos diferenciados (usuario estándar vs administrador).
    """
    def setUp(self):
        self.password = "ClaveSegura123!"
        self.operador = User.objects.create_user(
            username='operador1',
            password=self.password,
            email='op1@test.cl',
            is_staff=False
        )
        self.admin = User.objects.create_user(
            username='admin1',
            password=self.password,
            email='admin1@test.cl',
            is_staff=True
        )
        self.producto = Producto.objects.create(nombre="Harina", stock=50, precio=950.00)

    def test_emision_de_tokens_jwt(self):
        url = reverse('token_obtain_pair')
        payload = {'username': 'operador1', 'password': self.password}
        respuesta = self.client.post(url, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertIn('access', datos)
        self.assertIn('refresh', datos)

    def test_refresco_de_token_jwt(self):
        url_obtain = reverse('token_obtain_pair')
        respuesta_obtain = self.client.post(url_obtain, {'username': 'operador1', 'password': self.password}, format='json')
        refresh_token = respuesta_obtain.json()['refresh']

        url_refresh = reverse('token_refresh')
        respuesta_refresh = self.client.post(url_refresh, {'refresh': refresh_token}, format='json')

        self.assertEqual(respuesta_refresh.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta_refresh.json())

    def test_rechazo_sin_autenticacion_en_endpoint_protegido(self):
        url = reverse('despacho-solicitud')
        respuesta = self.client.post(url, {'producto_id': self.producto.id, 'cantidad_solicitada': 10}, format='json')
        # Debe rechazar con 401 Unauthorized
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        datos = respuesta.json()
        self.assertFalse(datos['exito'])
        self.assertEqual(datos['tipo_error'], 'NotAuthenticated')

    def test_permisos_diferenciados_usuario_vs_admin(self):
        # 1. Operador estándar NO puede crear productos en catálogo (POST /productos/)
        self.client.force_authenticate(user=self.operador)
        url_productos = reverse('producto-list')
        nuevo_prod = {'nombre': 'Fideos Tallarines', 'stock': 30, 'precio': 890.0}
        respuesta_op = self.client.post(url_productos, nuevo_prod, format='json')
        self.assertEqual(respuesta_op.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Administrador / Staff SÍ puede crear productos en catálogo
        self.client.force_authenticate(user=self.admin)
        respuesta_admin = self.client.post(url_productos, nuevo_prod, format='json')
        self.assertEqual(respuesta_admin.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta_admin.json()['nombre'], 'Fideos Tallarines')


class FormatoJSONYErroresTests(APITestCase):
    """
    Rúbrica 3.1.3: Verifica respuestas JSON estructuradas, manejo de errores
    estandarizado y filtros por campos de consulta.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='usuario_json', password='password123')
        self.client.force_authenticate(user=self.user)
        self.p1 = Producto.objects.create(nombre="Arroz Blanco", stock=100, precio=1200.0)
        self.p2 = Producto.objects.create(nombre="Lentejas", stock=40, precio=1500.0)

        MovimientoInventario.objects.create(
            producto=self.p1, cantidad_solicitada=10, stock_previo=100, stock_resultante=90,
            estado=MovimientoInventario.ESTADO_ACEPTADO, motivo="Aprobado", usuario=self.user
        )
        MovimientoInventario.objects.create(
            producto=self.p2, cantidad_solicitada=60, stock_previo=40, stock_resultante=40,
            estado=MovimientoInventario.ESTADO_RECHAZADO, motivo="Stock insuficiente", usuario=self.user
        )

    def test_manejo_de_errores_en_formato_json_estandarizado(self):
        # Intentar acceder a un producto inexistente produce 404 estructurado
        url = reverse('producto-detail', kwargs={'pk': 99999})
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        datos = respuesta.json()
        self.assertFalse(datos['exito'])
        self.assertEqual(datos['status_code'], 404)
        self.assertEqual(datos['tipo_error'], 'NotFound')
        self.assertIn('mensaje', datos)

    def test_filtrado_por_estado_en_movimientos(self):
        url = reverse('movimiento-list')
        respuesta = self.client.get(url, {'estado': 'Aceptado'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos['count'], 1)
        self.assertEqual(datos['results'][0]['estado'], 'Aceptado')

    def test_busqueda_de_productos_por_texto(self):
        url = reverse('producto-list')
        respuesta = self.client.get(url, {'search': 'Lentejas'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos['count'], 1)
        self.assertEqual(datos['results'][0]['nombre'], 'Lentejas')


class ApiRESTfulYReglasNegocioTests(APITestCase):
    """
    Rúbrica 3.1.4: Verifica la API RESTful completa (verbos HTTP, códigos de estado)
    y el cumplimiento riguroso de las 4 reglas de negocio de Ev1.
    """
    def setUp(self):
        self.admin = User.objects.create_superuser(username='super_rest', password='password123')
        self.operador = User.objects.create_user(username='op_rest', password='password123')
        self.client.force_authenticate(user=self.admin)
        self.producto = Producto.objects.create(nombre="arroz", stock=100, precio=1290.00)

    def test_operaciones_crud_completas_en_productos(self):
        # 1. GET lista (200 OK)
        res_list = self.client.get(reverse('producto-list'))
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        # 2. POST crear (201 Created)
        res_create = self.client.post(
            reverse('producto-list'),
            {'nombre': 'Sal Lobos 1kg', 'stock': 50, 'precio': 650.0},
            format='json'
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        nuevo_id = res_create.json()['id']

        # 3. GET detalle (200 OK)
        res_get = self.client.get(reverse('producto-detail', kwargs={'pk': nuevo_id}))
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        # 4. PUT actualizar completo (200 OK)
        res_put = self.client.put(
            reverse('producto-detail', kwargs={'pk': nuevo_id}),
            {'nombre': 'Sal Lobos Fina 1kg', 'stock': 45, 'precio': 700.0},
            format='json'
        )
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)
        self.assertEqual(res_put.json()['nombre'], 'Sal Lobos Fina 1kg')

        # 5. PATCH actualizar parcial (200 OK)
        res_patch = self.client.patch(
            reverse('producto-detail', kwargs={'pk': nuevo_id}),
            {'stock': 40},
            format='json'
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.json()['stock'], 40)

        # 6. DELETE eliminar (204 No Content)
        res_del = self.client.delete(reverse('producto-detail', kwargs={'pk': nuevo_id}))
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)

    def test_caso_1_invalido_cantidad_menor_o_igual_a_cero(self):
        # Regla 1: cantidad <= 0
        url = reverse('despacho-solicitud')
        payload = {'producto_id': self.producto.id, 'cantidad_solicitada': 0}
        respuesta = self.client.post(url, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        datos = respuesta.json()
        self.assertEqual(datos['estado'], 'Inválido')
        self.assertFalse(datos['exito'])
        self.assertIn("Error: La cantidad solicitada o el stock no pueden ser menores o iguales a cero.", datos['motivo'])
        
        # El stock en BD no debe variar
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 100)

    def test_caso_2_rechazado_excede_limite_maximo_50(self):
        # Regla 2: cantidad > 50
        url = reverse('despacho-solicitud')
        payload = {'producto_id': self.producto.id, 'cantidad_solicitada': 51}
        respuesta = self.client.post(url, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos['estado'], 'Rechazado')
        self.assertFalse(datos['exito'])
        self.assertIn("Excede el límite máximo de despacho", datos['motivo'])

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 100)

    def test_caso_3_rechazado_stock_insuficiente(self):
        # Regla 3: cantidad > stock
        prod_escaso = Producto.objects.create(nombre="Azúcar Morena", stock=15, precio=1100.0)
        url = reverse('despacho-solicitud')
        payload = {'producto_id': prod_escaso.id, 'cantidad_solicitada': 20}
        respuesta = self.client.post(url, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos['estado'], 'Rechazado')
        self.assertFalse(datos['exito'])
        self.assertIn("Stock insuficiente en bodega. Disponible: 15 unidades.", datos['motivo'])

        prod_escaso.refresh_from_db()
        self.assertEqual(prod_escaso.stock, 15)

    def test_caso_4_aceptado_y_descuento_atomico_de_stock(self):
        # Regla 4: cantidad <= stock y <= 50
        url = reverse('despacho-solicitud')
        payload = {'producto_id': self.producto.id, 'cantidad_solicitada': 20}
        respuesta = self.client.post(url, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        datos = respuesta.json()
        self.assertEqual(datos['estado'], 'Aceptado')
        self.assertTrue(datos['exito'])
        self.assertEqual(datos['stock_previo'], 100)
        self.assertEqual(datos['stock_resultante'], 80)
        self.assertIn("Solicitud aprobada y lista para despacho.", datos['motivo'])

        # Verificar que el stock se actualizó efectivamente en la base de datos
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 80)

    def test_vista_resumen_html_responde_exitosamente(self):
        respuesta = self.client.get(reverse('resumen'))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertContains(respuesta, "arroz")
