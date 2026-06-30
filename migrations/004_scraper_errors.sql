-- =============================================================
-- Migración 004: Tabla de errores del scraper
-- Solo para bases de datos existentes.
-- En entornos nuevos (Docker fresh start), SQLAlchemy crea
-- la tabla automáticamente via Base.metadata.create_all().
-- =============================================================

CREATE TABLE IF NOT EXISTS scraper_errors (
    id               SERIAL PRIMARY KEY,
    source           VARCHAR(50)  NOT NULL,
    station_name     VARCHAR(100),
    error_type       VARCHAR(50)  NOT NULL,
    http_status_code INTEGER,
    url              TEXT,
    error_message    TEXT         NOT NULL,
    occurred_at      TIMESTAMP    NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_scraper_errors_source      ON scraper_errors (source);
CREATE INDEX IF NOT EXISTS ix_scraper_errors_occurred_at ON scraper_errors (occurred_at);

-- Verificación
SELECT COUNT(*) AS registros_errores FROM scraper_errors;


-- =============================================================
-- QUERIES DE MONITOREO
-- =============================================================

-- Errores de las últimas 24 horas agrupados por fuente y tipo
-- SELECT source, error_type, COUNT(*) AS total
-- FROM scraper_errors
-- WHERE occurred_at >= NOW() - INTERVAL '24 hours'
-- GROUP BY source, error_type
-- ORDER BY total DESC;

-- Estaciones con más fallos en los últimos 7 días
-- SELECT source, station_name, COUNT(*) AS fallos
-- FROM scraper_errors
-- WHERE occurred_at >= NOW() - INTERVAL '7 days'
-- GROUP BY source, station_name
-- ORDER BY fallos DESC
-- LIMIT 20;

-- Últimos 50 errores con detalle completo
-- SELECT id, occurred_at, source, station_name, error_type, http_status_code, error_message
-- FROM scraper_errors
-- ORDER BY occurred_at DESC
-- LIMIT 50;

-- Tasa de error por fuente (últimas 24h)
-- SELECT source,
--        COUNT(*) AS total_errores,
--        MIN(occurred_at) AS primer_error,
--        MAX(occurred_at) AS ultimo_error
-- FROM scraper_errors
-- WHERE occurred_at >= NOW() - INTERVAL '24 hours'
-- GROUP BY source;
