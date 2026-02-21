# 🚀 LiveMenu Backend API - Quick Start Guide

## Inicio Rápido (3 pasos)

### 1. Generar certificados SSL
```bash
make dev-setup
# o manualmente:
bash generate-certs.sh
cp .env.example .env
```

### 2. Levantar servicios
```bash
make up
# o manualmente:
docker-compose up --build -d
```

### 3. Verificar que funciona
```bash
curl -k https://localhost/api/v1/auth/health
```

## Primer Uso - Ejemplo Completo

### 1. Registrar un usuario
```bash
curl -k -X POST https://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@livemenu.com",
    "password": "SecurePass123"
  }'
```

Guarda el `access_token` de la respuesta.

### 2. Crear un restaurante
```bash
curl -k -X POST https://localhost/api/v1/admin/restaurant \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TU_ACCESS_TOKEN>" \
  -d '{
    "name": "Mi Restaurante",
    "description": "Descripción de mi restaurante",
    "phone": "+1234567890"
  }'
```

### 3. Crear una categoría
```bash
curl -k -X POST https://localhost/api/v1/admin/categories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TU_ACCESS_TOKEN>" \
  -d '{
    "name": "Entradas",
    "description": "Platos de entrada",
    "active": true
  }'
```

Guarda el `id` de la categoría de la respuesta.

### 4. Crear un plato
```bash
curl -k -X POST https://localhost/api/v1/admin/dishes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TU_ACCESS_TOKEN>" \
  -d '{
    "category_id": "<CATEGORY_ID>",
    "name": "Ensalada César",
    "description": "Ensalada con pollo y aderezo césar",
    "price": "12.99",
    "available": true,
    "featured": true,
    "tags": ["saludable", "popular"]
  }'
```

### 5. Listar platos
```bash
curl -k https://localhost/api/v1/admin/dishes \
  -H "Authorization: Bearer <TU_ACCESS_TOKEN>"
```

## Comandos Útiles

```bash
# Ver logs
make logs

# Ejecutar tests
make test

# Crear nueva migración
make migrate-create NAME="add_new_table"

# Ejecutar migraciones
make migrate

# Abrir shell en API
make shell-api

# Abrir shell en DB
make shell-db

# Limpiar todo
make clean

# Reiniciar servicios
make restart
```

## Acceder a la Documentación

Si `ENABLE_DOCS=true` en tu `.env`:

- **Swagger UI**: https://localhost/docs
- **ReDoc**: https://localhost/redoc

## Troubleshooting

### Error: "SSL certificate problem"
Usa `-k` con curl para desarrollo (certificado self-signed)

### Error: "Connection refused"
Verifica que los servicios estén corriendo:
```bash
docker-compose ps
```

### Error de migraciones
Ejecuta manualmente:
```bash
docker-compose run --rm api alembic upgrade head
```

### Ver logs de errores
```bash
docker-compose logs -f api
```

## Producción

Para deployment en producción:

1. Genera certificados válidos (Let's Encrypt)
2. Actualiza `.env` con valores seguros:
   - `JWT_SECRET` (32+ caracteres aleatorios)
   - `IP_HASH_SALT` (32+ caracteres aleatorios)
   - `ENABLE_DOCS=false`
   - `APP_ENV=production`
3. Configura backup de PostgreSQL
4. Usa `docker-compose -f docker-compose.prod.yml up -d`

## Más información

Ver [README.md](README.md) para documentación completa.
