ALTER TABLE stations
    ADD COLUMN IF NOT EXISTS precipitation_enabled BOOLEAN NOT NULL DEFAULT FALSE;


CREATE TABLE IF NOT EXISTS precipitation_measurements (
    id           SERIAL  PRIMARY KEY,
    station_id   INTEGER NOT NULL REFERENCES stations(id),
    date_time    TIMESTAMP NOT NULL,
    precipitation FLOAT  NOT NULL,   -- precipitación horaria [mm]
    UNIQUE (station_id, date_time)
);

CREATE INDEX IF NOT EXISTS ix_precipitation_measurements_station_datetime
    ON precipitation_measurements (station_id, date_time DESC);
