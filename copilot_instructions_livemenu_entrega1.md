# LiveMenu API (Entrega 1) — Instrucciones para GitHub Copilot (generación completa)
> Objetivo: que GitHub Copilot genere TODO el backend **FastAPI + PostgreSQL + Docker** para los endpoints:
**Autenticación, Restaurantes, Categorías, Platos, Analytics**, exponiendo la API por **HTTPS** con **ciphers obligatorios**.

---

## 0) Contexto del enunciado (NO cambiar)
- Backend: **Python + FastAPI**
- DB: **PostgreSQL**
- Driver: **SQLAlchemy + asyncpg**
- Auth: **JWT (implementación propia)**
- Password hash: **bcrypt**
- Requerimientos NFR: **HTTPS**, **rate limiting 100 req/min**, estilo **ruff**, tests **pytest** (>=60% cobertura)
- Endpoints base especificados en el enunciado bajo `/api/v1/*`.
- Todas las rutas ` /api/v1/admin/* ` requieren header `Authorization: Bearer <JWT_TOKEN>`.

---

## 1) Alcance de lo que debes generar (Copilot)
Genera un proyecto backend **productivo y ejecutable** que incluya:

### 1.1 Endpoints requeridos
**Autenticación**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh` (opcional, PERO implementarlo)
- `POST /api/v1/auth/logout` (opcional, PERO implementarlo como invalidación de refresh token)

**Restaurante (admin)**
- `GET /api/v1/admin/restaurant`
- `POST /api/v1/admin/restaurant`
- `PUT /api/v1/admin/restaurant`
- `DELETE /api/v1/admin/restaurant`

**Categorías (admin)**
- `GET /api/v1/admin/categories`
- `POST /api/v1/admin/categories`
- `PUT /api/v1/admin/categories/{id}`
- `DELETE /api/v1/admin/categories/{id}`
- `PATCH /api/v1/admin/categories/reorder`

**Platos (admin)**
- `GET /api/v1/admin/dishes` (con filtros: category_id, available, featured, q(search), tags)
- `GET /api/v1/admin/dishes/{id}`
- `POST /api/v1/admin/dishes`
- `PUT /api/v1/admin/dishes/{id}`
- `DELETE /api/v1/admin/dishes/{id}` (soft delete)
- `PATCH /api/v1/admin/dishes/{id}/availability` (toggle)

**Analytics (admin)**
- `GET /api/v1/admin/analytics` (dashboard básico)
- `GET /api/v1/admin/analytics/export` (CSV)

> Nota: aunque el enunciado menciona otros módulos (menú público, QR, upload), **en esta entrega enfócate en los cinco módulos anteriores**. Aun así, deja la arquitectura preparada para extender a menú público / QR / upload sin refactor masivo.

---

## 2) Stack y librerías (fijar versiones razonables)
Genera `pyproject.toml` con:
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `SQLAlchemy>=2`
- `asyncpg`
- `alembic`
- `python-jose[cryptography]` (JWT)
- `passlib[bcrypt]` o `bcrypt` + util propio (preferible `passlib` por DX)
- `python-multipart` (por si luego agregan upload; no romperá)
- `structlog` o logging estándar (preferible `structlog`)
- `slowapi` o middleware propio para rate limit (si lo haces propio, documenta)
- `pytest`, `pytest-asyncio`, `httpx`, `coverage`
- `ruff`

---

## 3) Estructura de carpetas (obligatoria)
Crea la siguiente estructura (arquitectura por capas: handlers/services/repos):

```
api/
  app/
    main.py
    core/
      config.py
      logging.py
      security/
        jwt.py
        passwords.py
      middleware/
        auth.py
        rate_limit.py
        cors.py
        request_id.py
        errors.py
    models/
      user.py
      restaurant.py
      category.py
      dish.py
      scan_event.py
      refresh_token.py
    repositories/
      user_repo.py
      restaurant_repo.py
      category_repo.py
      dish_repo.py
      analytics_repo.py
      refresh_token_repo.py
    services/
      auth_service.py
      restaurant_service.py
      category_service.py
      dish_service.py
      analytics_service.py
    api/
      deps.py
      routers/
        auth.py
        restaurant.py
        categories.py
        dishes.py
        analytics.py
    schemas/
      auth.py
      restaurant.py
      category.py
      dish.py
      analytics.py
    utils/
      slug.py
      pagination.py
      csv_export.py
database/
  base.py
  session.py
  migrations/   # Alembic
    env.py
    versions/
tests/
  conftest.py
  test_auth.py
  test_restaurant.py
  test_categories.py
  test_dishes.py
  test_analytics.py
Dockerfile
docker-compose.yml
nginx/
  nginx.conf
  certs/
    server.crt
    server.key
.env.example
README.md
```

---

## 4) Modelo de datos (PostgreSQL) — tablas y reglas
Implementa modelos SQLAlchemy (async) con UUID (preferible `uuid.UUID` + `sqlalchemy.dialects.postgresql.UUID`).

### 4.1 Users
- `id` UUID PK
- `email` varchar unique not null (case-insensitive: guarda en lower())
- `password_hash` text not null
- `created_at`, `updated_at`

### 4.2 Restaurants
- `id` UUID PK
- `owner_user_id` UUID FK -> users.id (1 usuario tiene 0..1 restaurante en MVP)
- `name` varchar(100) not null
- `slug` varchar unique not null (generado desde name + sufijo si colisiona)
- `description` varchar(500) nullable
- `logo_url` text nullable
- `phone` text nullable
- `address` text nullable
- `hours` JSONB nullable
- `created_at`, `updated_at`

### 4.3 Categories
- `id` UUID PK
- `restaurant_id` UUID FK -> restaurants.id not null
- `name` varchar(50) not null
- `description` text nullable
- `position` int not null default 0
- `active` boolean not null default true
- `created_at`, `updated_at`
Reglas:
- listadas ordenadas por `position ASC, created_at ASC`
- delete: **solo si no tiene dishes activos**

### 4.4 Dishes
- `id` UUID PK
- `category_id` UUID FK -> categories.id not null
- `name` varchar(100) not null
- `description` varchar(300) nullable
- `price` numeric(10,2) not null
- `sale_price` numeric(10,2) nullable
- `image_url` text nullable
- `available` boolean not null default true
- `featured` boolean not null default false
- `tags` text[] nullable (Postgres array)
- `position` int not null default 0
- `created_at`, `updated_at`
- `deleted_at` timestamptz nullable (soft delete)
Reglas:
- El listado por defecto excluye soft-deleted (`deleted_at is null`)
- Toggle availability: invierte `available`

### 4.5 Scan events (para Analytics)
Tabla `scan_events`:
- `id` UUID PK
- `restaurant_id` UUID FK -> restaurants.id not null
- `timestamp` timestamptz not null default now()
- `user_agent` text not null
- `ip_hash` text not null (anonimizado: sha256(ip + salt))
- `referrer` text nullable

> Aunque en MVP no implementamos el endpoint público del menú, **sí genera la tabla** para que Analytics funcione. Agrega un método util para insertar eventos desde un futuro endpoint público.

### 4.6 Refresh tokens (para logout real)
Tabla `refresh_tokens`:
- `id` UUID PK
- `user_id` UUID FK -> users.id not null
- `token_hash` text not null (hash de refresh token, nunca guardar en claro)
- `revoked_at` timestamptz nullable
- `expires_at` timestamptz not null
- `created_at` timestamptz not null default now()
Reglas:
- Logout: marca tokens activos como revocados
- Refresh: valida que exista token_hash y no esté revocado y no expirado

---

## 5) Autenticación y autorización (JWT)
Implementa:
- Access token (JWT) corto: 15 min
- Refresh token largo: 7 días
- Algoritmo: HS256 con `JWT_SECRET`
- Claims mínimos:
  - `sub`: user_id (UUID string)
  - `email`
  - `exp`, `iat`, `nbf`
  - `type`: "access" / "refresh"

Middleware / dependency:
- Para todas rutas `/api/v1/admin/*`, valida bearer token (access).
- Si el token expira: responder `401` con payload claro (ej: `{ "detail": "token_expired" }`)

---

## 6) Reglas de negocio por endpoint (detallado)
### 6.1 Auth
**POST /auth/register**
- Input: email, password
- Validaciones:
  - email formato válido
  - password: min 8, al menos 1 letra y 1 número (simple)
- Normalizar email a lower-case
- Si email ya existe -> 409
- Guarda password con bcrypt
- Respuesta: user + tokens (access + refresh)

**POST /auth/login**
- Verifica credenciales
- Si falla -> 401
- Respuesta: tokens

**POST /auth/refresh**
- Input: refresh_token
- Valida refresh_token JWT (type refresh)
- Valida token_hash en DB y no revocado/expirado
- Emite nuevo access (y opcionalmente rota refresh: RECOMENDADO rotar)
- Respuesta: tokens

**POST /auth/logout**
- Requiere access token
- Invalida/Revoca refresh tokens del usuario (o el refresh token provisto)
- Respuesta: 204

### 6.2 Restaurant
**Regla MVP**: 1 usuario -> 0..1 restaurante.
- `GET`: si no existe -> 404
- `POST`: si ya existe -> 409
- `PUT`: actualiza campos permitidos; si cambia `name`, recalcula slug (y asegura unicidad)
- `DELETE`: elimina restaurante **y cascada controlada**:
  - Opción A: soft delete (recomendado)
  - Opción B: hard delete con cascade (categories/dishes) (aceptable si documentas)
Mantén consistencia transaccional.

### 6.3 Categories
- List: solo categorías del restaurante del usuario autenticado
- Create: asigna `position` al final (max+1)
- Update: permite name/description/active/position
- Delete: si tiene dishes no eliminados -> 409
- Reorder: input `{ "ordered_ids": [uuid, uuid, ...] }` y reasigna posiciones 0..n-1 en una transacción.

### 6.4 Dishes
- List: filtros por query params:
  - `category_id`, `available`, `featured`, `q`, `tag`, `min_price`, `max_price`
  - paginación `limit` (default 20) y `offset` (default 0)
- Get by id: valida pertenencia al restaurante del usuario (join category->restaurant)
- Create: valida category pertenece al restaurante
- Update: idem, y si mueve category, valida category destino
- Delete: set `deleted_at = now()`
- Availability: toggle boolean

### 6.5 Analytics
**GET /admin/analytics**
Retorna JSON con:
- total_scans_all_time
- scans_by_period (día/semana/mes según query `granularity=day|week|month` default day)
- scans_by_hour (0..23) para el rango
- top_user_agents (top 5) opcional
Query params:
- `from` (ISO date) opcional
- `to` (ISO date) opcional

**GET /admin/analytics/export**
- Mismo filtro de rango
- Responde `text/csv` descargable con columnas:
  - timestamp, user_agent, ip_hash, referrer

---

## 7) Middlewares obligatorios
Implementa en `app/main.py` (orden recomendado):

1) `Request ID` (genera `X-Request-Id` si no viene)
2) `Structured Logging` (log request/response básico)
3) `CORS` (configurable por env)
4) `Rate limiting`:
   - 100 req/min por IP para rutas `/api/v1/admin/*` (y auth también)
   - Respuesta 429 con detalle
5) `Error Handling` (formato uniforme)
6) `JWT Validation` como dependency en routers admin (no como middleware global para no afectar rutas públicas futuras)

---

## 8) Migraciones (Alembic) y seed opcional
- Configura Alembic para async SQLAlchemy.
- Genera migración inicial que cree todas las tablas.
- Incluye comando en README:
  - `alembic upgrade head` al arrancar contenedor (entrypoint o comando compose)

---

## 9) HTTPS con ciphers obligatorios (Docker + Nginx reverse proxy)
### 9.1 Arquitectura TLS
Termina TLS en **Nginx** y reenvía a FastAPI por HTTP interno.

Servicios:
- `nginx` (443) -> proxy a `api:8000`
- `api` (8000) sin exponer directo a host (solo en red interna)
- `db` (5432) sin exponer a host (opcional exponer para debug)

### 9.2 Ciphers obligatorios (configurar Nginx)
En `nginx/nginx.conf` configura:
- Protocolos: `TLSv1.2 TLSv1.3`
- TLS 1.3 cipher suites:
  - `TLS_AES_256_GCM_SHA384`
  - `TLS_AES_128_GCM_SHA256`
  - `TLS_CHACHA20_POLY1305_SHA256`
- TLS 1.2 cipher list (solo fuertes, ECDHE + GCM):
  - `ECDHE-ECDSA-AES256-GCM-SHA384`
  - `ECDHE-RSA-AES256-GCM-SHA384`
  - `ECDHE-ECDSA-AES128-GCM-SHA256`
  - `ECDHE-RSA-AES128-GCM-SHA256`
  - `ECDHE-ECDSA-CHACHA20-POLY1305`
  - `ECDHE-RSA-CHACHA20-POLY1305`
- Deshabilita ciphers débiles, compresión, renegociación insegura.
- Security headers mínimos:
  - `Strict-Transport-Security` (para dev puedes desactivar, pero deja listo)
  - `X-Content-Type-Options nosniff`
  - `X-Frame-Options DENY`
  - `Referrer-Policy no-referrer`
  - `Content-Security-Policy` (mínima)

### 9.3 Certificado dev (self-signed)
Incluye un script o instrucción en README para generar:
- `nginx/certs/server.crt`
- `nginx/certs/server.key`
Ejemplo (documentar):
- `openssl req -x509 -nodes -days 365 -newkey rsa:2048 ...`

> En producción se usaría Let’s Encrypt o cert corporativo; pero para la entrega, self-signed es suficiente.

---

## 10) Dockerfile y docker-compose (obligatorio)
### 10.1 Dockerfile (api/Dockerfile)
- Base: `python:3.12-slim`
- Instala dependencias con cache (poetry o pip). Preferible `pip` + `requirements` desde `pyproject` usando `pip install .`
- Copia código
- Expone 8000
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 10.2 docker-compose.yml
Incluye:
- `db` con volumen persistente
- `api` con env vars para DB, JWT, etc.
- `nginx` con montajes de `nginx.conf` y `certs`, publica `443:443`
Red interna: `backend`

---

## 11) Variables de entorno (crear .env.example)
Incluye al menos:
- `APP_ENV=dev`
- `APP_NAME=livemenu-api`
- `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`
- `DATABASE_URL=postgresql+asyncpg://livemenu:livemenu@db:5432/livemenu`
- `JWT_SECRET=change-me`
- `JWT_ACCESS_TTL_MIN=15`
- `JWT_REFRESH_TTL_DAYS=7`
- `IP_HASH_SALT=change-me-too`
- `RATE_LIMIT_PER_MINUTE=100`
- `LOG_LEVEL=INFO`

---

## 12) Calidad: ruff + tests
### 12.1 Ruff
- Agrega configuración ruff en `pyproject.toml`
- `make lint` opcional

### 12.2 Tests
- Usa `pytest-asyncio` y `httpx.AsyncClient` para probar endpoints.
- Usa DB de test (puede ser sqlite in-memory NO, porque array/jsonb; mejor levantar Postgres con docker-compose override o fixture que use el mismo db con schema separado).
- Asegura pruebas mínimas:
  - register/login/refresh/logout
  - create restaurant + get/update/delete
  - category CRUD + reorder
  - dish CRUD + soft delete + availability
  - analytics vacío + export CSV con 0 filas
- Cobertura >= 60% (documenta `pytest --cov`)

---

## 13) Requisitos extra (DX)
- Documenta todo en `README.md`:
  - cómo levantar con docker
  - cómo correr migraciones
  - cómo correr tests
  - cómo probar HTTPS (curl -k https://localhost/api/v1/...)
- Habilita docs de FastAPI en:
  - `/docs` y `/redoc` (solo en dev, configurable por env)
- Respuestas de error uniformes:
  - `{ "detail": "<code>", "message": "<human readable>", "request_id": "..." }`

---

## 14) Paso a paso para Copilot (modo ejecución)
> Copilot: sigue estos pasos estrictamente y crea los archivos en el orden.

1) Crear estructura de carpetas y `pyproject.toml`.
2) Implementar config (`core/config.py`) y logging.
3) Implementar DB async session + base + models.
4) Configurar Alembic async + migración inicial.
5) Implementar repositorios (CRUD) por entidad.
6) Implementar services (reglas de negocio) por módulo.
7) Implementar routers + schemas pydantic.
8) Implementar middlewares (rate limit, request id, error handler).
9) Integrar todo en `main.py`.
10) Agregar tests.
11) Crear `Dockerfile`, `docker-compose.yml` y `nginx/nginx.conf` con TLS + ciphers.
12) Crear `.env.example` y `README.md`.

---

## 15) Checklist final (antes de cerrar PR)
- [ ] `docker-compose up --build` levanta: `nginx` en 443, `api` y `db` ok
- [ ] `curl -k https://localhost/api/v1/auth/health` (agrega endpoint health simple) responde 200
- [ ] `curl -k https://localhost/api/v1/auth/register ...` funciona
- [ ] Rutas `/api/v1/admin/*` exigen JWT
- [ ] Rate limiting 100 req/min activo (429)
- [ ] Migraciones se aplican automáticamente o documentadas
- [ ] `pytest` pasa y cobertura >= 60%
- [ ] `ruff check .` pasa

---

## 16) Nota importante
No inventes endpoints fuera del enunciado para estos módulos (excepto `health`). Mantén el prefijo y métodos tal cual.
