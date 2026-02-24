# LiveMenu Backend API

Backend API para LiveMenu construido con FastAPI, PostgreSQL y Docker, exponiendo endpoints HTTPS con ciphers seguros.

## 🚀 Características

- **FastAPI** con async/await para alto rendimiento
- **PostgreSQL** con SQLAlchemy 2.0 y asyncpg
- **Autenticación JWT** con refresh tokens
- **Rate limiting** de 100 req/min por IP
- **HTTPS** con TLS 1.2/1.3 y ciphers seguros configurados en Nginx
- **Migraciones** con Alembic
- **Tests** con pytest (>60% cobertura)
- **Linting** con ruff
- **Docker** y docker-compose para deployment

## 📋 Requisitos

- Docker y Docker Compose
- Python 3.12+ (para desarrollo local)
- OpenSSL (para generar certificados)

## 🛠️ Instalación y Ejecución

### 1. Generar Certificados SSL

Primero, genera certificados SSL self-signed para desarrollo:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/C=US/ST=State/L=City/O=LiveMenu/CN=localhost"
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y ajusta los valores:

```bash
cp .env.example .env
```

**Importante:** En producción, cambia `JWT_SECRET` e `IP_HASH_SALT` a valores seguros y aleatorios.

### 3. Levantar con Docker Compose

```bash
docker-compose up --build
```

Esto levantará:
- **PostgreSQL** en puerto interno 5432
- **API** en puerto interno 8000
- **Nginx** en puerto **443** (HTTPS)

### 4. Verificar que funciona

Prueba el endpoint de health:

```bash
curl -k https://localhost/api/v1/auth/health
```

Deberías ver: `{"status":"ok"}`

## 📚 Documentación de la API

Si `ENABLE_DOCS=true` en `.env`:

- **Swagger UI**: https://localhost/docs
- **ReDoc**: https://localhost/redoc

## 🗄️ Migraciones de Base de Datos

Las migraciones se ejecutan automáticamente al iniciar el contenedor. Para ejecutarlas manualmente:

```bash
# Dentro del contenedor
docker exec -it livemenu-api alembic upgrade head

# O localmente (requiere Python y dependencias instaladas)
alembic upgrade head
```

Para crear una nueva migración:

```bash
alembic revision --autogenerate -m "descripcion del cambio"
```

## 🧪 Tests

### Ejecutar tests localmente

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html
```

### Ejecutar tests en Docker

```bash
docker-compose run --rm api pytest
```

## 🔒 Seguridad

### TLS/SSL Configuration

El servidor **solo acepta HTTPS** en puerto 443 con la siguiente configuración:

**Protocolos soportados:**
- TLS 1.2
- TLS 1.3

**TLS 1.3 Cipher Suites:**
- `TLS_AES_256_GCM_SHA384`
- `TLS_AES_128_GCM_SHA256`
- `TLS_CHACHA20_POLY1305_SHA256`

**TLS 1.2 Cipher Suites:**
- `ECDHE-ECDSA-AES256-GCM-SHA384`
- `ECDHE-RSA-AES256-GCM-SHA384`
- `ECDHE-ECDSA-AES128-GCM-SHA256`
- `ECDHE-RSA-AES128-GCM-SHA256`
- `ECDHE-ECDSA-CHACHA20-POLY1305`
- `ECDHE-RSA-CHACHA20-POLY1305`

**Security Headers:**
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Content-Security-Policy`

### Autenticación

- **Access Token**: JWT válido por 15 minutos
- **Refresh Token**: Válido por 7 días, rotado en cada refresh
- Todas las rutas `/api/v1/admin/*` requieren header `Authorization: Bearer <token>`

### Rate Limiting

- **100 requests/minuto** por IP
- Aplica a todas las rutas (auth y admin)
- Respuesta `429 Too Many Requests` cuando se excede

## 📁 Estructura del Proyecto

```
api/
  app/
    main.py              # Aplicación FastAPI principal
    core/                # Configuración, logging, seguridad
    models/              # Modelos SQLAlchemy
    repositories/        # Capa de acceso a datos
    services/            # Lógica de negocio
    api/
      routers/           # Endpoints FastAPI
      deps.py            # Dependencias de inyección
    schemas/             # Schemas Pydantic
    utils/               # Utilidades (slug, CSV, etc.)
database/
  base.py                # Declarative Base de SQLAlchemy
  session.py             # Configuración de sesión async
  migrations/            # Migraciones de Alembic
    env.py
    versions/
tests/                   # Tests con pytest
nginx/                   # Configuración Nginx + TLS
docker-compose.yml       # Orquestación de servicios
```
  tests/                 # Tests con pytest
nginx/
  nginx.conf             # Configuración Nginx con TLS
  certs/                 # Certificados SSL
docker-compose.yml       # Orquestación de servicios
Dockerfile               # Imagen de la API
alembic.ini              # Configuración de migraciones
pyproject.toml           # Dependencias y config de Python
```

## 🎯 Endpoints Principales

### Autenticación (`/api/v1/auth`)

- `POST /register` - Registro de usuario
- `POST /login` - Login
- `POST /refresh` - Refrescar access token
- `POST /logout` - Logout (requiere auth)

### Restaurante (`/api/v1/admin/restaurant`) 🔒

- `GET /` - Obtener restaurante del usuario
- `POST /` - Crear restaurante
- `PUT /` - Actualizar restaurante
- `DELETE /` - Eliminar restaurante

### Categorías (`/api/v1/admin/categories`) 🔒

- `GET /` - Listar categorías
- `POST /` - Crear categoría
- `PUT /{id}` - Actualizar categoría
- `DELETE /{id}` - Eliminar categoría
- `PATCH /reorder` - Reordenar categorías

### Platos (`/api/v1/admin/dishes`) 🔒

- `GET /` - Listar platos (con filtros)
- `GET /{id}` - Obtener plato
- `POST /` - Crear plato
- `PUT /{id}` - Actualizar plato
- `DELETE /{id}` - Eliminar plato (soft delete)
- `PATCH /{id}/availability` - Toggle disponibilidad

### Analytics (`/api/v1/admin/analytics`) 🔒

- `GET /` - Dashboard de analytics
- `GET /export` - Exportar datos a CSV

🔒 = Requiere autenticación (Bearer token)

## 🔧 Desarrollo Local (sin Docker)

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Levantar PostgreSQL (o usar Docker para solo DB)
docker-compose up db

# Configurar .env con DATABASE_URL apuntando a localhost
# DATABASE_URL=postgresql+asyncpg://livemenu:livemenu@localhost:5432/livemenu

# Ejecutar migraciones
alembic upgrade head

# Levantar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Code Quality

### Linting con Ruff

```bash
ruff check .
```

### Formateo

```bash
ruff format .
```

## 📊 Modelo de Datos

- **Users**: Usuarios autenticados
- **Restaurants**: Un restaurante por usuario (1:1)
- **Categories**: Categorías de menú (con orden)
- **Dishes**: Platos (soft delete, con posición)
- **ScanEvents**: Eventos de escaneo QR (para analytics)
- **RefreshTokens**: Tokens de refresh almacenados (para logout)

## 🚀 Deployment a Producción

1. **Generar certificados válidos** (Let's Encrypt o certificado corporativo)
2. **Actualizar variables de entorno**:
   - Cambiar `JWT_SECRET` y `IP_HASH_SALT` a valores seguros
   - Configurar `DATABASE_URL` con credenciales de producción
   - `ENABLE_DOCS=false` para desactivar Swagger
   - `APP_ENV=production`
3. **Configurar CORS** con los origins permitidos
4. **Revisar security headers** en nginx.conf según requisitos
5. **Usar volúmenes persistentes** para PostgreSQL
6. **Configurar backups** de la base de datos

## 📝 Licencia

Este proyecto es parte del curso de Seguridad Cloud.

## 👥 Autores

Desarrollado para el Proyecto 1 - Seguridad Cloud
