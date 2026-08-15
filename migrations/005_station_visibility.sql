-- =============================================================
-- Migración 005: Visibilidad de estaciones en el frontend
-- Aplica solo a bases de datos con datos existentes.
-- En entornos nuevos (Docker fresh start), SQLAlchemy crea
-- las tablas con el esquema nuevo directamente.
-- =============================================================

-- Agregar columna is_visible con default TRUE para que todas las
-- estaciones existentes queden visibles sin intervención manual.
ALTER TABLE stations ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT TRUE;
