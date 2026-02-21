# ✅ Checklist de Validación - LiveMenu API

## Pre-deployment

### Configuración
- [ ] Certificados SSL generados (`nginx/certs/server.crt` y `server.key`)
- [ ] Archivo `.env` creado desde `.env.example`
- [ ] Variables `JWT_SECRET` y `IP_HASH_SALT` cambiadas a valores seguros (producción)
- [ ] `CORS_ORIGINS` configurado con los dominios permitidos
- [ ] `ENABLE_DOCS=false` en producción

### Infraestructura
- [ ] Docker y Docker Compose instalados
- [ ] Puertos 443 (HTTPS) y 5432 (PostgreSQL) disponibles
- [ ] Volúmenes de PostgreSQL configurados para persistencia

## Deployment

### Build y Start
- [ ] `docker-compose build` ejecutado sin errores
- [ ] `docker-compose up -d` levanta todos los servicios
- [ ] Servicio `db` saludable (healthcheck pasa)
- [ ] Servicio `api` saludable (healthcheck pasa)
- [ ] Servicio `nginx` saludable y escuchando en 443

### Verificación de Servicios
```bash
# Verificar que todos los servicios están corriendo
docker-compose ps

# Debería mostrar:
# - livemenu-db (healthy)
# - livemenu-api (healthy)
# - livemenu-nginx (healthy)
```

## Funcionalidad

### 1. Health Check
```bash
curl -k https://localhost/api/v1/auth/health
# Esperado: {"status":"ok"}
```
- [ ] Health check responde 200 OK

### 2. Registro de Usuario
```bash
curl -k -X POST https://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
- [ ] Registro exitoso (201 Created)
- [ ] Retorna `user`, `access_token`, `refresh_token`
- [ ] Email duplicado retorna 409 Conflict
- [ ] Password débil retorna 422 Validation Error

### 3. Login
```bash
curl -k -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
- [ ] Login exitoso (200 OK)
- [ ] Credenciales inválidas retornan 401 Unauthorized

### 4. Refresh Token
```bash
curl -k -X POST https://localhost/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<TOKEN>"}'
```
- [ ] Refresh exitoso con tokens válidos
- [ ] Token inválido retorna 401

### 5. Endpoints Protegidos (con Authorization header)
- [ ] `GET /api/v1/admin/restaurant` sin token retorna 401
- [ ] Con token válido funciona correctamente
- [ ] Token expirado retorna 401 con detail "token_expired"

### 6. CRUD Restaurante
- [ ] POST crear restaurante (201)
- [ ] GET obtener restaurante (200)
- [ ] PUT actualizar restaurante (200)
- [ ] DELETE eliminar restaurante (204)
- [ ] Crear segundo restaurante para mismo usuario retorna 409

### 7. CRUD Categorías
- [ ] POST crear categoría (201)
- [ ] GET listar categorías (200)
- [ ] PUT actualizar categoría (200)
- [ ] DELETE categoría sin platos (204)
- [ ] DELETE categoría con platos activos (409)
- [ ] PATCH reordenar categorías (204)

### 8. CRUD Platos
- [ ] POST crear plato (201)
- [ ] GET listar platos con paginación (200)
- [ ] GET plato por ID (200)
- [ ] PUT actualizar plato (200)
- [ ] DELETE soft delete plato (200 con deleted_at)
- [ ] PATCH toggle availability (200)
- [ ] Filtros funcionan (category_id, available, featured, q, tag)

### 9. Analytics
- [ ] GET analytics dashboard (200)
- [ ] GET analytics/export retorna CSV (200)
- [ ] Sin datos retorna estructura correcta con valores en 0

### 10. Rate Limiting
```bash
# Ejecutar 101 requests rápidos
for i in {1..101}; do
  curl -k https://localhost/api/v1/auth/health
done
```
- [ ] Después de 100 requests/min retorna 429 Too Many Requests

## Seguridad

### TLS/SSL
```bash
# Verificar protocolos y ciphers
openssl s_client -connect localhost:443 -tls1_2 < /dev/null
openssl s_client -connect localhost:443 -tls1_3 < /dev/null
```
- [ ] TLS 1.2 funciona
- [ ] TLS 1.3 funciona
- [ ] Ciphers configurados correctamente
- [ ] Headers de seguridad presentes en respuestas

### Headers de Seguridad
```bash
curl -k -I https://localhost/api/v1/auth/health
```
Verificar presencia de:
- [ ] `Strict-Transport-Security`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `Referrer-Policy: no-referrer`
- [ ] `Content-Security-Policy`
- [ ] `X-Request-Id`

### Autenticación
- [ ] Passwords hasheados con bcrypt
- [ ] JWT con claims correctos (sub, email, type, exp, iat, nbf)
- [ ] Access token expira en 15 min
- [ ] Refresh token expira en 7 días
- [ ] Refresh token rotation funciona (logout invalida tokens)

## Tests

### Ejecutar Suite de Tests
```bash
make test
# o
docker-compose run --rm api pytest
```
- [ ] Todos los tests pasan
- [ ] test_auth.py (8+ tests)
- [ ] test_restaurant.py (5+ tests)
- [ ] test_categories.py (5+ tests)
- [ ] test_dishes.py (6+ tests)
- [ ] test_analytics.py (2+ tests)

### Cobertura
```bash
make test-cov
# o
docker-compose run --rm api pytest --cov=app --cov-report=html
```
- [ ] Cobertura >= 60%

## Migraciones

### Base de Datos
```bash
docker-compose exec db psql -U livemenu -d livemenu -c "\dt"
```
Verificar que existen las tablas:
- [ ] users
- [ ] restaurants
- [ ] categories
- [ ] dishes
- [ ] scan_events
- [ ] refresh_tokens
- [ ] alembic_version

## Documentación

### API Docs (solo en desarrollo)
Si `ENABLE_DOCS=true`:
- [ ] https://localhost/docs accesible (Swagger UI)
- [ ] https://localhost/redoc accesible (ReDoc)
- [ ] Todos los endpoints documentados
- [ ] Schemas de request/response correctos

## Code Quality

### Linting
```bash
make lint
```
- [ ] Sin errores de ruff

### Formato
```bash
make format
```
- [ ] Código formateado correctamente

## Logs

### Verificación de Logs
```bash
docker-compose logs api | grep ERROR
```
- [ ] Sin errores críticos en logs
- [ ] Request logging funciona
- [ ] Structured logging configurado

## Performance

### Respuestas
- [ ] Health check < 50ms
- [ ] Endpoints auth < 200ms
- [ ] Endpoints CRUD < 300ms
- [ ] Analytics < 500ms

## Cleanup

### Después de Testing
```bash
make clean
```
- [ ] Contenedores detenidos
- [ ] Volúmenes limpiados
- [ ] Imágenes huérfanas eliminadas

## Producción Extra

### Antes de ir a Producción
- [ ] Certificados SSL de CA confiable (Let's Encrypt)
- [ ] Backup automático de PostgreSQL configurado
- [ ] Monitoreo y alertas configurados
- [ ] Logs centralizados
- [ ] Variables de entorno seguras (secrets management)
- [ ] Rate limiting ajustado según carga esperada
- [ ] CDN configurado si es necesario
- [ ] Health checks en balanceador de carga

---

## Resumen de Comandos Útiles

```bash
# Setup inicial
make dev-setup

# Levantar servicios
make up

# Ver logs
make logs

# Ejecutar tests
make test

# Ejecutar migraciones
make migrate

# Limpiar todo
make clean

# Verificar salud
curl -k https://localhost/api/v1/auth/health
```

¡Checklist completado! ✅
