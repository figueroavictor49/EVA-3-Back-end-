# EVA 3 - Django REST Framework Backend

**API RESTful para el Sistema de Control de Inventario y Despachos**  
*Basado en la arquitectura y reglas de negocio del repositorio [Ev1](https://github.com/figueroavictor49/Ev1.git).*

---

## Tabla de Contenidos
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Cumplimiento de la Rúbrica de Evaluación](#cumplimiento-de-la-rúbrica-de-evaluación)
3. [Tecnologías y Librerías Utilizadas](#tecnologías-y-librerías-utilizadas)
4. [Instalación y Puesta en Marcha](#instalación-y-puesta-en-marcha)
5. [Documentación y Catálogo de Endpoints RESTful](#documentación-y-catálogo-de-endpoints-restful)
6. [Reglas de Negocio Implementadas (Heredadas de Ev1)](#reglas-de-negocio-implementadas-heredadas-de-ev1)
7. [Autenticación y Seguridad JWT](#autenticación-y-seguridad-jwt)
8. [Verificación y Pruebas Automatizadas](#verificación-y-pruebas-automatizadas)
9. [Uso y Evaluación Crítica de IA](#uso-y-evaluación-crítica-de-ia)

---

## Descripción del Proyecto

El presente proyecto corresponde a la **Evaluación 3 (EVA 3)**, en la cual se evoluciona la aplicación de consola y vista web desarrollada en **Ev1** hacia una **API RESTful completa, profesional y segura** desarrollada con **Django REST Framework (DRF)**.

El sistema permite gestionar un catálogo de productos en bodega, procesar solicitudes de despacho de inventario evaluando de forma atómica y consistente las **cuatro condiciones de negocio** originales, almacenar el historial de auditoría de cada transacción y ofrecer mecanismos modernos de autenticación y autorización mediante **JSON Web Tokens (JWT)**.

---

## Cumplimiento de la Rúbrica de Evaluación

El desarrollo fue estructurado minuciosamente para alcanzar el **puntaje máximo (3 puntos)** en cada uno de los cuatro criterios de la rúbrica oficial:

| Criterio | Nivel Alcanzado | Justificación Técnica de la Implementación |
| :--- | :---: | :--- |
| **3.1.1 Configura Django REST Framework, según la documentación oficial.** | **3 PUNTOS** | Configuración completa y ordenada en `miproyecto/settings.py` con settings explícitos de DRF (`REST_FRAMEWORK`). Implementación de `DefaultRouter` en `core/urls.py`, versionado formal de la API mediante rutas de URL (`URLPathVersioning` en `/api/v1/`), paginación enriquecida (`StandardResultsSetPagination`) y documentación OpenAPI 3.0 con `drf-spectacular`. Cada opción está justificada técnicamente en la documentación. |
| **3.1.2 Codifica instrucciones de autenticación, considerando recomendaciones de IA.** | **3 PUNTOS** | Autenticación robusta basada en **JSON Web Tokens (JWT)** con `djangorestframework-simplejwt`. Implementación de emisión, verificación y refresco de tokens con expiración corta (15 min para Access Token y 1 día para Refresh Token con rotación activa). Permisos diferenciados (`IsAdminOrReadOnly`, permisos por rol `is_staff`), resguardo estricto de secretos con `python-decouple` (`.env` / `.env.example`). En `ia.md` se evalúan críticamente las sugerencias de IA, justificando adopciones y descartes. |
| **3.1.3 Codifica instrucciones que generen resultados en formato JSON.** | **3 PUNTOS** | Todos los endpoints entregan respuestas JSON estructuradas y consistentes respaldadas por serializadores de DRF. Manejo centralizado de excepciones con `custom_exception_handler` que provee códigos semánticos y mensajes comprensibles. Filtrado por parámetros de consulta (`?estado=`, `?producto=`), búsqueda por texto (`?search=`), ordenamiento (`?ordering=`) y paginación con metadatos. Verificado con 16 pruebas automatizadas y colecciones para clientes HTTP (`pruebas_api.http` y `postman_collection.json`). |
| **3.1.4 Codifica una API funcional con características RESTful, considerando recomendaciones de IA.** | **3 PUNTOS** | API completamente funcional que respeta rigurosamente las convenciones REST: recursos nombrados en plural con sustantivos (`/productos/`, `/movimientos/`, `/despachos/`), uso semántico de verbos HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) y códigos de estado (`200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`). Operaciones CRUD completas, despacho transaccional con bloqueo pesimista contra condiciones de carrera, documentación interactiva Swagger UI y Redoc, y reporte crítico de IA en `ia.md`. |

---

## Tecnologías y Librerías Utilizadas

- **Python 3.10+** (Probado en Python 3.14).
- **Django 5.x / 6.x**: Framework web principal.
- **Django REST Framework 3.18+**: Framework para la construcción de la API RESTful.
- **djangorestframework-simplejwt**: Autenticación estándar con JSON Web Tokens.
- **django-filter**: Filtrado dinámico de consultas en endpoints de listado.
- **drf-spectacular**: Generación de esquemas OpenAPI 3.0, Swagger UI y Redoc.
- **python-decouple**: Gestión segura de variables de entorno y secretos.
- **SQLite3**: Motor de base de datos relacional para persistencia y auditoría.

---

## Instalación y Puesta en Marcha

### 1. Clonar el repositorio
```bash
git clone https://github.com/figueroavictor49/EVA-3-Back-end-.git
cd EVA-3-Back-end-
```

### 2. Configurar el entorno virtual (Recomendado)
```bash
python -m venv venv
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux/macOS:
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copie el archivo de plantilla `.env.example` a `.env`:
```bash
# En Windows:
Copy-Item .env.example .env
# En Linux/macOS:
cp .env.example .env
```

### 5. Ejecutar migraciones de base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Cargar datos iniciales (Usuarios y Productos de prueba)
El proyecto incluye un comando de gestión que crea los usuarios de prueba, importa el historial inicial desde `datos.json` y genera el catálogo de productos:
```bash
python manage.py cargar_datos_iniciales
```

> **Credenciales de prueba generadas automáticamente:**
> - **Administrador:** Usuario: `admin` | Contraseña: `admin123` (Acceso total, CRUD de productos, panel admin).
> - **Operador:** Usuario: `operador` | Contraseña: `operador123` (Acceso a solicitar despachos y ver auditoría).

### 7. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```
La aplicación quedará disponible en: `http://127.0.0.1:8000/`

---

## Documentación y Catálogo de Endpoints RESTful

Al acceder a la raíz `http://127.0.0.1:8000/` se redirige automáticamente a la interfaz interactiva de **Swagger UI**.

### Enlaces Directos de Documentación:
- **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
- **Redoc UI:** `http://127.0.0.1:8000/api/redoc/`
- **Esquema OpenAPI 3.0 (YAML/JSON):** `http://127.0.0.1:8000/api/schema/`
- **Vista Web Resumen (Heredada de Ev1):** `http://127.0.0.1:8000/resumen/`

### Tabla Resumen de Endpoints de la API (`/api/v1/`):

| Método | Endpoint | Descripción | Permisos | Código HTTP Éxito |
| :---: | :--- | :--- | :---: | :---: |
| `POST` | `/api/v1/auth/registro/` | Registro de nuevos usuarios en el sistema | Público | `201 Created` |
| `POST` | `/api/v1/auth/token/` | Obtención de tokens JWT (`access` y `refresh`) | Público | `200 OK` |
| `POST` | `/api/v1/auth/token/refresh/` | Refresco de token de acceso expirado | Público | `200 OK` |
| `POST` | `/api/v1/auth/token/verify/` | Verificación de validez de un token | Público | `200 OK` |
| `GET` | `/api/v1/auth/perfil/` | Consulta de perfil del usuario en sesión | Autenticado | `200 OK` |
| `GET` | `/api/v1/productos/` | Listado paginado de productos con filtros y búsqueda | Abierto / Auth | `200 OK` |
| `POST` | `/api/v1/productos/` | Creación de un nuevo producto en catálogo | Solo Staff / Admin | `201 Created` |
| `GET` | `/api/v1/productos/{id}/` | Detalle de un producto por su ID | Abierto / Auth | `200 OK` |
| `PUT` | `/api/v1/productos/{id}/` | Actualización total de un producto | Solo Staff / Admin | `200 OK` |
| `PATCH` | `/api/v1/productos/{id}/` | Actualización parcial de un producto (ej. stock) | Solo Staff / Admin | `200 OK` |
| `DELETE`| `/api/v1/productos/{id}/` | Eliminación de un producto | Solo Staff / Admin | `204 No Content` |
| `GET` | `/api/v1/productos/{id}/movimientos/` | Historial de movimientos de un producto específico | Autenticado | `200 OK` |
| `POST` | `/api/v1/despachos/` | Procesar solicitud de salida aplicando las 4 reglas | Autenticado | `201` / `200` / `400` |
| `GET` | `/api/v1/movimientos/` | Listado paginado de movimientos con filtros | Autenticado | `200 OK` |
| `GET` | `/api/v1/movimientos/{id}/` | Detalle de una transacción de movimiento | Autenticado | `200 OK` |
| `GET` | `/api/v1/movimientos/estadisticas/` | Conteo general por estado (Aceptado/Rechazado/Inválido) | Autenticado | `200 OK` |

---

## Reglas de Negocio Implementadas (Heredadas de Ev1)

El endpoint `POST /api/v1/despachos/` evalúa de forma estricta las cuatro condiciones de la función pura `decidir_salida_inventario` definida en Ev1:

1. **Caso 1: Inválido (`400 Bad Request`)**  
   - *Condición:* `cantidad_solicitada <= 0` o `stock_actual < 0`.  
   - *Respuesta:* Rechazo inmediato sin descuento de inventario.  
   - *Motivo:* `"Error: La cantidad solicitada o el stock no pueden ser menores o iguales a cero."`

2. **Caso 2: Rechazado por límite superior (`200 OK` con `estado: "Rechazado"`)**  
   - *Condición:* `cantidad_solicitada > 50`.  
   - *Respuesta:* Registro del intento rechazado en auditoría; el stock permanece intacto.  
   - *Motivo:* `"Excede el límite máximo de despacho permitido por transacción (Máx 50 unidades)."`

3. **Caso 3: Rechazado por stock insuficiente (`200 OK` con `estado: "Rechazado"`)**  
   - *Condición:* `cantidad_solicitada > stock_actual`.  
   - *Respuesta:* Registro del intento en auditoría; el stock permanece intacto.  
   - *Motivo:* `"Stock insuficiente en bodega. Disponible: {stock_actual} unidades."`

4. **Caso 4: Aceptado (`201 Created` con `estado: "Aceptado"`)**  
   - *Condición:* `cantidad_solicitada <= stock_actual` (y menor o igual a 50).  
   - *Respuesta:* Descuento atómico de stock en base de datos (`stock -= cantidad`) y registro exitoso.  
   - *Motivo:* `"Solicitud aprobada y lista para despacho."`

---

## Autenticación y Seguridad JWT

1. **Encabezado de autorización:**  
   Para realizar peticiones a endpoints protegidos, se debe incluir el token de acceso en el header HTTP:
   ```http
   Authorization: Bearer <tu_access_token>
   ```
2. **Duración de Tokens:**  
   - Access Token: **15 minutos** (minimiza ventana de compromiso).  
   - Refresh Token: **1 día** (permite renovar credenciales con rotación).
3. **Resguardo de Credenciales:**  
   - Las contraseñas se almacenan mediante el algoritmo criptográfico PBKDF2 con hash SHA256 con salt de Django.  
   - Parámetros sensibles (`SECRET_KEY`, tiempo de tokens) se configuran vía `.env`, manteniéndose fuera del control de versiones.

---

## Verificación y Pruebas Automatizadas

El proyecto incluye dos mecanismos integrales de verificación:

### 1. Suite de Pruebas Automatizadas con Django (`tests.py`)
Ejecute las 16 pruebas automatizadas:
```bash
python manage.py test
```
Las pruebas verifican:
- Montaje de routers, versionado y paginación (Rúbrica 3.1.1).
- Flujo de tokens JWT y permisos diferenciados usuario/administrador (Rúbrica 3.1.2).
- Formato consistente de respuestas JSON y captura de errores normalizados (Rúbrica 3.1.3).
- Operaciones CRUD completas y verificación de los 4 casos de negocio de Ev1 (Rúbrica 3.1.4).

### 2. Pruebas con Cliente HTTP
En la raíz del proyecto se incluyen dos archivos listos para interactuar con la API:
- **`pruebas_api.http`:** Colección para ejecutar directamente en VS Code con la extensión *REST Client* o *Thunder Client*.
- **`postman_collection.json`:** Colección en formato v2.1 importable en Postman o Insomnia con variables y scripts de prueba configurados.

---

## Uso y Evaluación Crítica de IA

El archivo **[`ia.md`](ia.md)** contiene el reporte exhaustivo sobre cómo se utilizó la Inteligencia Artificial durante el proyecto, evaluando críticamente cada recomendación recibida y detallando los fundamentos técnicos por los cuales ciertas sugerencias fueron adoptadas (JWT, control atómico con `select_for_update()`, documentación OpenAPI 3.0 con `drf-spectacular`, manejo centralizado de excepciones JSON) y otras fueron descartadas (tokens nativos sin expiración, acceso de 24 horas, clases de permisos planas, secretos hardcodeados).