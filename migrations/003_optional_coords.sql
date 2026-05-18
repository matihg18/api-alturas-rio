-- =============================================================
-- Migración 003: Coordenadas opcionales en stations
-- Hace que latitud y longitud sean nullable para soportar
-- estaciones sin coordenadas publicadas (ej. fuente CARU).
--
-- En entornos nuevos (Docker fresh start), SQLAlchemy crea
-- las tablas con el esquema nuevo directamente.
-- Ejecutar este script solo sobre bases de datos existentes.
-- =============================================================

ALTER TABLE stations ALTER COLUMN latitud DROP NOT NULL;
ALTER TABLE stations ALTER COLUMN longitud DROP NOT NULL;

-- Verificación
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'stations'
  AND column_name IN ('latitud', 'longitud');
