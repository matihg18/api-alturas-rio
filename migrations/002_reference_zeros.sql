-- =============================================================
-- Migración 002: Ceros de Referencia Hidrológicos
-- Crea el catálogo de datums, los puntos físicos de medición
-- y los offsets para las estaciones del Río Uruguay (PDF).
--
-- En entornos nuevos (Docker fresh start), SQLAlchemy crea
-- las tablas directamente. Ejecutar este script solo sobre
-- bases de datos existentes.
-- =============================================================

-- 1. Catálogo de tipos de datum (IGN y WHARTON en v1)
CREATE TABLE reference_zero_types (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO reference_zero_types (code, name, description) VALUES
    ('IGN',     'Cero IGN',     'Instituto Geográfico Nacional de Argentina'),
    ('WHARTON', 'Cero Wharton', 'Sistema de referencia Wharton (río Uruguay)');

-- 2. Puntos físicos de medición
CREATE TABLE gauge_points (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    river       VARCHAR(50),
    description TEXT
);

INSERT INTO gauge_points (name, river) VALUES
    ('Monte Caseros',              'Uruguay'),
    ('Bella Unión',                'Uruguay'),
    ('Mocoretá',                   'Uruguay'),
    ('Federación',                 'Uruguay'),
    ('Federación Embalse',         'Uruguay'),
    ('Salto Grande Aguas Arriba',  'Uruguay'),
    ('Salto Grande Aguas Abajo',   'Uruguay'),
    ('Salto',                      'Uruguay'),
    ('Concordia',                  'Uruguay'),
    ('Colón',                      'Uruguay'),
    ('Paysandú',                   'Uruguay'),
    ('Concepción del Uruguay',     'Uruguay'),
    ('Campichuelo',                'Uruguay'),
    ('Fray Bentos',                'Uruguay'),
    ('Boca del Gualeguaychú',      'Uruguay'),
    ('Nueva Palmira',              'Uruguay');

-- 3. FK nullable en stations
ALTER TABLE stations ADD COLUMN gauge_point_id INTEGER REFERENCES gauge_points(id);

-- 4. Offsets por gauge_point y datum
CREATE TABLE gauge_datums (
    id                    SERIAL PRIMARY KEY,
    gauge_point_id        INTEGER NOT NULL REFERENCES gauge_points(id),
    datum_type_id         INTEGER NOT NULL REFERENCES reference_zero_types(id),
    offset_local_to_datum FLOAT NOT NULL,
    UNIQUE (gauge_point_id, datum_type_id)
);

-- Offsets IGN (fuente: Estudio_CerosRU, columna "Diferencias Cero Local a Cero IGN")
INSERT INTO gauge_datums (gauge_point_id, datum_type_id, offset_local_to_datum)
VALUES
    ((SELECT id FROM gauge_points WHERE name = 'Monte Caseros'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 32.71),
    ((SELECT id FROM gauge_points WHERE name = 'Bella Unión'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 32.88),
    ((SELECT id FROM gauge_points WHERE name = 'Mocoretá'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 25.58),
    ((SELECT id FROM gauge_points WHERE name = 'Federación'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 31.73),
    ((SELECT id FROM gauge_points WHERE name = 'Federación Embalse'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.52),
    ((SELECT id FROM gauge_points WHERE name = 'Salto Grande Aguas Arriba'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.52),
    ((SELECT id FROM gauge_points WHERE name = 'Salto Grande Aguas Abajo'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.52),
    ((SELECT id FROM gauge_points WHERE name = 'Salto'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.69),
    ((SELECT id FROM gauge_points WHERE name = 'Concordia'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 1.29),
    ((SELECT id FROM gauge_points WHERE name = 'Colón'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 0.03),
    ((SELECT id FROM gauge_points WHERE name = 'Paysandú'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 0.33),
    ((SELECT id FROM gauge_points WHERE name = 'Concepción del Uruguay'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.05),
    ((SELECT id FROM gauge_points WHERE name = 'Campichuelo'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.08),
    ((SELECT id FROM gauge_points WHERE name = 'Fray Bentos'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.14),
    ((SELECT id FROM gauge_points WHERE name = 'Boca del Gualeguaychú'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), -0.18),
    ((SELECT id FROM gauge_points WHERE name = 'Nueva Palmira'),
     (SELECT id FROM reference_zero_types WHERE code = 'IGN'), 0.03);

-- Offsets WHARTON (fuente: Estudio_CerosRU, columna "Diferencias Cero Local a Cero Wharton")
INSERT INTO gauge_datums (gauge_point_id, datum_type_id, offset_local_to_datum)
VALUES
    ((SELECT id FROM gauge_points WHERE name = 'Monte Caseros'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 33.40),
    ((SELECT id FROM gauge_points WHERE name = 'Bella Unión'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 33.57),
    ((SELECT id FROM gauge_points WHERE name = 'Mocoretá'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 26.27),
    ((SELECT id FROM gauge_points WHERE name = 'Federación'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 32.42),
    ((SELECT id FROM gauge_points WHERE name = 'Federación Embalse'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.17),
    ((SELECT id FROM gauge_points WHERE name = 'Salto Grande Aguas Arriba'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.17),
    ((SELECT id FROM gauge_points WHERE name = 'Salto Grande Aguas Abajo'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.17),
    ((SELECT id FROM gauge_points WHERE name = 'Salto'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.00),
    ((SELECT id FROM gauge_points WHERE name = 'Concordia'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 1.98),
    ((SELECT id FROM gauge_points WHERE name = 'Colón'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.72),
    ((SELECT id FROM gauge_points WHERE name = 'Paysandú'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 1.02),
    ((SELECT id FROM gauge_points WHERE name = 'Concepción del Uruguay'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.64),
    ((SELECT id FROM gauge_points WHERE name = 'Campichuelo'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.61),
    ((SELECT id FROM gauge_points WHERE name = 'Fray Bentos'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.55),
    ((SELECT id FROM gauge_points WHERE name = 'Boca del Gualeguaychú'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.51),
    ((SELECT id FROM gauge_points WHERE name = 'Nueva Palmira'),
     (SELECT id FROM reference_zero_types WHERE code = 'WHARTON'), 0.72);

-- Verificación
SELECT 'reference_zero_types' AS tabla, COUNT(*) AS registros FROM reference_zero_types
UNION ALL
SELECT 'gauge_points', COUNT(*) FROM gauge_points
UNION ALL
SELECT 'gauge_datums', COUNT(*) FROM gauge_datums;
