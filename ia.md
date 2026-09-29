# Informe de Uso y Evaluación Crítica de Inteligencia Artificial
**Proyecto:** EVA 3 - Django REST Framework Backend  
**Base del Proyecto:** Repositorio Ev1 (`https://github.com/figueroavictor49/Ev1.git`)  
**Repositorio Destino:** EVA-3-Back-end- (`https://github.com/figueroavictor49/EVA-3-Back-end-.git`)  
**Autor:** Victor Figueroa  

---

## 1. Contexto y Objetivos de la Consulta a IA

Para el desarrollo de la Evaluación 3, se utilizó una herramienta de Inteligencia Artificial como consultor arquitectónico y de seguridad, orientada al cumplimiento de los cuatro criterios de la rúbrica oficial:

1. **Rúbrica 3.1.1:** Configuración completa y ordenada de Django REST Framework (routers, versionado, paginación y settings explícitos).
2. **Rúbrica 3.1.2:** Autenticación robusta, permisos diferenciados, rotación/expiración de tokens, resguardo de credenciales y evaluación crítica de recomendaciones de IA.
3. **Rúbrica 3.1.3:** Generación de respuestas JSON consistentes, manejo estructurado de errores, filtrado, paginación y verificación en cliente HTTP.
4. **Rúbrica 3.1.4:** API funcional con características RESTful, operaciones CRUD, atomismo en despacho de inventario y documentación interactiva.

A continuación se documenta el análisis crítico de las recomendaciones emitidas por la IA, explicitando cuáles fueron adoptadas, cuáles fueron descartadas y sus fundamentos técnicos.

---

## 2. Evaluación Crítica en Autenticación y Seguridad (Rúbrica 3.1.2)

### 2.1 Elección del Mecanismo de Autenticación: JWT vs. TokenAuth vs. SessionAuth

* **Recomendación preliminar de la IA:**  
  La IA propuso inicialmente utilizar `rest_framework.authentication.TokenAuthentication` nativo de Django, argumentando menor complejidad de configuración al requerir únicamente la app `rest_framework.authtoken`.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA** la recomendación de `TokenAuthentication` nativo.  
  *Justificación:* El token estándar de DRF se almacena en la base de datos de manera estática y no posee mecanismo nativo de expiración ni de refresco, lo que representa una vulnerabilidad severa: si un token es interceptado, permanece válido indefinidamente hasta su revocación manual.  
* **Propuesta Alternativa Adoptada:**  
  Se adoptó **JSON Web Tokens (JWT)** mediante la librería oficial `djangorestframework-simplejwt`. Con esto, la autenticación es verdaderamente *stateless* (sin sobrecarga de lectura en base de datos para cada verificación de firma) y cumple con el estándar industrial RFC 7519.

### 2.2 Política de Expiración y Refresco de Tokens

* **Recomendación de la IA:**  
  Configurar un tiempo de expiración del token de acceso (`ACCESS_TOKEN_LIFETIME`) de 24 horas para "evitar que los usuarios deban iniciar sesión constantemente".
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA** la expiración de 24 horas por atentar contra el principio de mínimo privilegio y resguardo ante fugas.  
* **Decisión Adoptada:**  
  Se implementó un esquema de dos capas:
  1. **Access Token de corta duración (15 minutos):** Minimiza la ventana de exposición en caso de robo de credenciales en tránsito.
  2. **Refresh Token de duración media (1 día) con rotación activa (`ROTATE_REFRESH_TOKENS = True`):** Cada vez que se solicita un nuevo access token, el cliente recibe además un nuevo refresh token, invalidando de facto el anterior y previniendo ataques de repetición (*replay attacks*).

### 2.3 Permisos Diferenciados: Roles vs. Permiso Único

* **Recomendación de la IA:**  
  Proteger todos los endpoints aplicando simplemente `permission_classes = [IsAuthenticated]`.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA** por insuficiente. Si todos los usuarios autenticados tienen el mismo nivel de acceso, un bodeguero u operador común podría borrar productos del catálogo o modificar precios y stocks sin autorización.
* **Decisión Adoptada:**  
  Se diseñaron clases de permisos diferenciados en `core/permissions.py`:
  - `IsAdminOrReadOnly`: Permite a operadores autenticados consultar productos (métodos seguros `GET`), pero restringe la creación (`POST`), modificación (`PUT`/`PATCH`) y eliminación (`DELETE`) a usuarios con rol `is_staff` o `is_superuser`.
  - Los endpoints de despacho (`/api/v1/despachos/`) y auditoría (`/api/v1/movimientos/`) exigen autenticación JWT válida, asociando automáticamente la identidad del usuario que ejecutó la transacción (`request.user`).

### 2.4 Resguardo de Credenciales y Secretos

* **Recomendación de la IA:**  
  Utilizar un archivo de configuración estándar en Python con `SECRET_KEY = "django-insecure-..."` hardcodeado en `settings.py`.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA** tajantemente. Hardcodear secretos en repositorios de control de versiones viola la metodología *The Twelve-Factor App* (Factor III: Config).
* **Decisión Adoptada:**  
  Se integró `python-decouple` para desacoplar parámetros sensibles. El proyecto lee `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y tiempos de expiración desde variables de entorno provistas por un archivo `.env`. Se configuró `.gitignore` para impedir que `.env` sea rastreado por Git, proveyendo en su lugar `.env.example` como plantilla pública y segura.

---

## 3. Evaluación Crítica en Arquitectura RESTful y Formato JSON (Rúbricas 3.1.1, 3.1.3 y 3.1.4)

### 3.1 Centralización de Errores y Estandarización de Respuestas JSON

* **Recomendación de la IA:**  
  Permitir que DRF entregue sus mensajes de error por defecto (que varían entre listas de strings, diccionarios de campos o strings simples según el tipo de excepción).
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA**. La falta de una estructura uniforme de error dificulta la integración en clientes HTTP, interfaces web y aplicaciones móviles.
* **Decisión Adoptada:**  
  Se implementó un manejador global personalizado (`custom_exception_handler` en `core/exceptions.py`) registrado en `REST_FRAMEWORK['EXCEPTION_HANDLER']`. Todas las respuestas de error entregan un formato uniforme:
  ```json
  {
    "exito": false,
    "status_code": 404,
    "tipo_error": "NotFound",
    "mensaje": "El recurso solicitado no fue encontrado.",
    "detalles": { "detail": "No Producto matches the given query." }
  }
  ```

### 3.2 Concurrencia y Control Transaccional en Despachos

* **Recomendación de la IA:**  
  Leer el stock del producto mediante `Producto.objects.get(id=pk)`, evaluar las reglas y guardar con `producto.stock -= cantidad; producto.save()`.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA**. En un entorno multi-usuario, dos peticiones concurrentes de despacho sobre el mismo producto generarían una condición de carrera (*race condition* / *lost update*), provocando sobreventas y stocks negativos en bodega.
* **Decisión Adoptada:**  
  Se implementó en `core/services.py` el método `procesar_despacho` encapsulado en una transacción atómica de base de datos (`transaction.atomic()`) utilizando bloqueo pesimista a nivel de fila mediante `select_for_update()`:
  ```python
  with transaction.atomic():
      producto = Producto.objects.select_for_update().get(id=producto_id)
      # Evaluación de las 4 reglas de negocio de Ev1
      ...
  ```
  Esto garantiza propiedades ACID completas en el flujo transaccional.

### 3.3 Documentación de la API: OpenAPI 3.0 vs. Swagger 2.0 Antiguo

* **Recomendación de la IA:**  
  Instalar `django-rest-swagger` o `drf-yasg`.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA**. `django-rest-swagger` fue descontinuado y `drf-yasg` presenta serias incompatibilidades con versiones recientes de Django (4.x, 5.x y 6.x) al generar esquemas obsoletos de Swagger 2.0.
* **Decisión Adoptada:**  
  Se adoptó **`drf-spectacular`**, el estándar moderno recomendado oficialmente por Django REST Framework para generar esquemas OpenAPI 3.0 dinámicos, ofreciendo interfaces interactivas Swagger UI (`/api/docs/`) y Redoc (`/api/redoc/`).

### 3.4 Paginación y Filtrado

* **Recomendación de la IA:**  
  Implementar paginación básica por offset o dejar la paginación deshabilitada por defecto.
* **Evaluación Crítica y Decisión:**  
  **DESCARTADA**. Entregar colecciones sin paginar satura la memoria del servidor y el ancho de banda del cliente cuando el volumen de datos crece.
* **Decisión Adoptada:**  
  Se configuró `PageNumberPagination` enriquecida (`StandardResultsSetPagination` en `core/pagination.py`), la cual expone en formato JSON metadatos cuantitativos (`count`, `total_pages`, `current_page`, `page_size`, `next`, `previous`, `results`) y soporta personalización mediante parámetros en la URL (`?page=1&page_size=5`).

---

## 4. Matriz Comparativa de Recomendaciones de IA

| Área | Recomendación Inicial de IA | Decisión Adoptada | Justificación Técnica |
| :--- | :--- | :--- | :--- |
| **Autenticación** | Token Auth nativo de DRF | **JWT (SimpleJWT)** | El token nativo no tiene expiración ni refresco; JWT es stateless y robusto. |
| **Expiración de Tokens** | Access Token de 24 horas | **15 min Access + 1 día Refresh con rotación** | Reduce la superficie de ataque y previene replay attacks. |
| **Permisos** | `IsAuthenticated` global | **`IsAdminOrReadOnly` y permisos por rol** | Diferenciación de privilegios: sólo administradores pueden modificar catálogo. |
| **Credenciales** | Claves hardcodeadas en código | **`python-decouple` + `.env` + `.gitignore`** | Cumplimiento del Factor III de The Twelve-Factor App y resguardo de secretos. |
| **Concurrencia Stock** | Consulta y guardado simple | **`transaction.atomic()` + `select_for_update()`** | Previene condiciones de carrera y sobreventas en accesos concurrentes. |
| **Formato de Errores** | Respuestas nativas de DRF | **`custom_exception_handler` uniforme** | Estructura JSON estándar y predecible para clientes HTTP. |
| **Documentación** | `drf-yasg` / Swagger 2.0 | **`drf-spectacular` / OpenAPI 3.0** | Soporte moderno de estándares abiertos compatible con Django actual. |

---

## 5. Verificación de la Pertinencia mediante Pruebas Automatizadas

La efectividad de las recomendaciones adoptadas fue validada mediante una suite de 16 pruebas automatizadas (`core/tests.py`) ejecutadas con el cliente de pruebas `rest_framework.test.APITestCase`:

1. **Configuración DRF y Routers:** Verificación de rutas de ViewSets, formato de contenido `application/json` y metadatos de paginación.
2. **Seguridad y JWT:** Emisión de pares de tokens, renovación exitosa mediante endpoint de refresco y rechazo con código 401 de peticiones no autorizadas.
3. **Permisos Diferenciados:** Confirmación de que operadores reciben código 403 Forbidden al intentar crear productos y administradores reciben código 201 Created.
4. **Respuestas JSON y Errores:** Validación de formato estructurado en errores 404 y filtros por estado de movimiento.
5. **RESTful y Reglas de Ev1:** Verificación de los 4 casos de negocio:
   - *Caso 1 (Inválido):* Cantidad <= 0 -> Código 400 Bad Request.
   - *Caso 2 (Rechazado):* Cantidad > 50 -> Código 200 con estado 'Rechazado' y stock intacto.
   - *Caso 3 (Rechazado):* Cantidad > stock -> Código 200 con estado 'Rechazado' y stock intacto.
   - *Caso 4 (Aceptado):* Cantidad válida -> Código 201 Created, estado 'Aceptado' y descuento atómico del stock.

Resultado de la verificación: **16/16 pruebas superadas (OK)**.
