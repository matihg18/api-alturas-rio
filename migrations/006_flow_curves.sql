CREATE TABLE discharge_curve_params (
    id          SERIAL  PRIMARY KEY,
    station_id  INTEGER NOT NULL REFERENCES stations(id) UNIQUE,
    a           FLOAT   NOT NULL,
    b           FLOAT   NOT NULL,
    h0          FLOAT   NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE TABLE flow_measurements (
    id          SERIAL  PRIMARY KEY,
    station_id  INTEGER NOT NULL REFERENCES stations(id),
    date_time   TIMESTAMP NOT NULL,
    flow        FLOAT   NOT NULL,   -- caudal estimado [m³/s]
    UNIQUE (station_id, date_time)
);

CREATE INDEX ix_flow_measurements_station_datetime
    ON flow_measurements (station_id, date_time DESC);


INSERT INTO discharge_curve_params (station_id, a, b, h0, notes, created_at, updated_at) VALUES
    ((SELECT id FROM stations WHERE name = 'EL SOBERBIO'        AND source = 'prefectura'),
     643.10, 1.331, -0.005, 'EL SOBERBIO — Ajuste May-Ago 2026, R²=1.00000', NOW(), NOW()),
    ((SELECT id FROM stations WHERE name = 'SAN JAVIER'         AND source = 'prefectura'),
     500.39, 1.639, -0.005, 'SAN JAVIER — Ajuste May-Ago 2026, R²=1.00000',  NOW(), NOW()),
    ((SELECT id FROM stations WHERE name = 'GARRUCHOS'          AND source = 'prefectura'),
      70.07, 1.978, -3.228, 'GARRUCHOS — Ajuste May-Ago 2026, R²=0.99913',   NOW(), NOW()),
    ((SELECT id FROM stations WHERE name = 'SANTO TOME'         AND source = 'prefectura'),
      39.11, 2.246, -2.469, 'SANTO TOME — Ajuste May-Ago 2026, R²=0.99997',  NOW(), NOW()),
    ((SELECT id FROM stations WHERE name = 'ALVEAR'             AND source = 'prefectura'),
       0.212, 3.964, -6.786, 'ALVEAR — Ajuste May-Ago 2026, R²=1.00000',     NOW(), NOW()),
    ((SELECT id FROM stations WHERE name = 'PASO DE LOS LIBRES' AND source = 'prefectura'),
     218.51, 1.840, -1.307, 'PASO DE LOS LIBRES — Ajuste May-Ago 2026, R²=0.99950', NOW(), NOW())
ON CONFLICT DO NOTHING;


SELECT s.name, d.a, d.b, d.h0, d.notes
FROM discharge_curve_params d
JOIN stations s ON s.id = d.station_id
ORDER BY s.name;
