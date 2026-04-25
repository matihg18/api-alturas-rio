-- =============================================================
-- Migración: Port → Station
-- Aplica solo a bases de datos con datos existentes.
-- En entornos nuevos (Docker fresh start), SQLAlchemy crea
-- las tablas con el esquema nuevo directamente.
-- =============================================================

-- 1. Renombrar tabla port → stations
ALTER TABLE port RENAME TO stations;

-- 2. Renombrar columna port_id → station_id en measurements
ALTER TABLE measurements RENAME COLUMN port_id TO station_id;

-- 3. Agregar columna source con default 'prefectura' para registros existentes
ALTER TABLE stations ADD COLUMN source VARCHAR(50) NOT NULL DEFAULT 'prefectura';

-- 4. Ampliar columna name para soportar nombres más largos (INA puede tener >50 chars)
ALTER TABLE stations ALTER COLUMN name TYPE VARCHAR(100);

-- Verificación
SELECT 'stations' AS tabla, COUNT(*) AS registros FROM stations
UNION ALL
SELECT 'measurements', COUNT(*) FROM measurements;
