-- LiveMenu — schema inicial (equivalente a la migración alembic 1ee53ca6855a)
-- Para aplicar desde la consola GCP: Cloud SQL → instancia → Cloud SQL Studio → pegar y ejecutar.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── users ───────────────────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at    TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at    TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

-- ── refresh_tokens ──────────────────────────────────────────────────────
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL,
    revoked_at  TIMESTAMP WITH TIME ZONE,
    expires_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX        ix_refresh_tokens_expires_at ON refresh_tokens (expires_at);
CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);
CREATE INDEX        ix_refresh_tokens_user_id    ON refresh_tokens (user_id);

-- ── restaurants ─────────────────────────────────────────────────────────
CREATE TABLE restaurants (
    id            UUID PRIMARY KEY,
    owner_user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name          VARCHAR(100) NOT NULL,
    slug          VARCHAR(150) NOT NULL,
    description   VARCHAR(500),
    logo_url      TEXT,
    phone         VARCHAR(50),
    address       TEXT,
    hours         JSONB,
    created_at    TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at    TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE UNIQUE INDEX ix_restaurants_owner_user_id ON restaurants (owner_user_id);
CREATE UNIQUE INDEX ix_restaurants_slug          ON restaurants (slug);

-- ── categories ──────────────────────────────────────────────────────────
CREATE TABLE categories (
    id            UUID PRIMARY KEY,
    restaurant_id UUID NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    name          VARCHAR(50) NOT NULL,
    description   TEXT,
    position      INTEGER NOT NULL,
    active        BOOLEAN NOT NULL,
    created_at    TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at    TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX ix_categories_restaurant_id ON categories (restaurant_id);

-- ── scan_events ─────────────────────────────────────────────────────────
CREATE TABLE scan_events (
    id            UUID NOT NULL,
    restaurant_id UUID NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    timestamp     TIMESTAMP WITH TIME ZONE NOT NULL,
    user_agent    TEXT NOT NULL,
    ip_hash       VARCHAR(64) NOT NULL,
    referrer      TEXT,
    PRIMARY KEY (id)
);
CREATE INDEX ix_scan_events_restaurant_id ON scan_events (restaurant_id);
CREATE INDEX ix_scan_events_timestamp     ON scan_events (timestamp);

-- ── dishes ──────────────────────────────────────────────────────────────
CREATE TABLE dishes (
    id          UUID PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(300),
    price       NUMERIC(10, 2) NOT NULL,
    sale_price  NUMERIC(10, 2),
    image_url   TEXT,
    available   BOOLEAN NOT NULL,
    featured    BOOLEAN NOT NULL,
    tags        TEXT[],
    position    INTEGER NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at  TIMESTAMP WITH TIME ZONE
);
CREATE INDEX ix_dishes_category_id ON dishes (category_id);
CREATE INDEX ix_dishes_deleted_at  ON dishes (deleted_at);

-- ── alembic version tracker ─────────────────────────────────────────────
-- Sin esta tabla, si más adelante alguien corre alembic, intentará crear todo
-- de nuevo. Marcamos la revisión actual como aplicada.
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('1ee53ca6855a');

COMMIT;
