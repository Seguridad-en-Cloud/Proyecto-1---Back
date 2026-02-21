# Cambios de Estructura: database/ fuera de api/

## Resumen
Se movió el directorio de base de datos desde `api/app/db/` a `database/` al mismo nivel que `api/`.

## Estructura Anterior
```
api/
  app/
    db/
      base.py
      session.py
      migrations/
```

## Estructura Nueva
```
database/
  base.py
  session.py
  migrations/
    env.py
    script.py.mako
    versions/
api/
  app/
    ... (resto del código)
```

## Archivos Modificados

### 1. Nuevos archivos creados en `database/`
- `database/__init__.py`
- `database/base.py`
- `database/session.py`
- `database/migrations/__init__.py`
- `database/migrations/env.py`
- `database/migrations/script.py.mako`

### 2. Importaciones actualizadas (de `app.db` a `database`)

**Modelos:**
- `api/app/models/user.py`
- `api/app/models/restaurant.py`
- `api/app/models/category.py`
- `api/app/models/dish.py`
- `api/app/models/scan_event.py`
- `api/app/models/refresh_token.py`

Cambio: `from app.db.base import Base` → `from database.base import Base`

**Dependencias:**
- `api/app/api/deps.py`

Cambio: `from app.db.session import get_session` → `from database.session import get_session`

**Tests:**
- `tests/conftest.py`

Cambios:
- `from app.db.base import Base` → `from database.base import Base`
- `from app.db.session import get_session` → `from database.session import get_session`

**Migraciones:**
- `database/migrations/env.py`

Cambio: `from app.db.base import Base` → `from database.base import Base`

### 3. Archivos de configuración actualizados

**alembic.ini:**
```ini
# Antes:
script_location = api/app/db/migrations

# Después:
script_location = database/migrations
```

**Dockerfile:**
```dockerfile
# Antes:
COPY api/ ./api/
COPY alembic.ini ./

# Después:
COPY api/ ./api/
COPY database/ ./database/
COPY alembic.ini ./
```

### 4. Documentación actualizada

**README.md:**
- Actualizada la sección "Estructura del Proyecto" para reflejar `database/` como directorio separado

**copilot_instructions_livemenu_entrega1.md:**
- Actualizada la sección 3 con la estructura correcta

### 5. Directorio eliminado
- `api/app/db/` (completo)

## Verificación

✅ No quedan referencias a `app.db` en el código
✅ Todos los imports apuntan a `database`
✅ Estructura de directorios correcta
✅ Alembic configurado para usar `database/migrations`
✅ Dockerfile copia el directorio `database/`

## Comandos para Verificar

```bash
# Verificar que no hay referencias a app.db
grep -r "from app.db" api/ tests/ database/

# Verificar que database/ existe
ls -la database/

# Verificar contenido de migraciones
ls -la database/migrations/

# Verificar que api/app/db no existe
ls api/app/db  # Debería dar error "No such file or directory"
```

## Próximos Pasos

El proyecto está listo para ejecutarse con:
```bash
docker-compose up --build
```

Las migraciones se ejecutarán automáticamente desde `database/migrations/`.
