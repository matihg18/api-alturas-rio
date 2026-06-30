from datetime import datetime
import scraper.config as config
from scraper.repository import ScraperRepository
from scraper.schemas import RawStationData, RawMeasurementData
from common.models import Station, Measurement


def test_sync_stations_creates_new_station(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    stations = [
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ]

    repo.sync_stations(stations)

    result = db_session.query(Station).all()
    assert len(result) == 1
    assert result[0].name == "COLON"
    assert result[0].latitud == -32.22
    assert result[0].longitud == -58.13


def test_sync_stations_updates_existing_station(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    stations_v1 = [
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13,
            ALERTA="7.10"
        )
    ]
    repo.sync_stations(stations_v1)

    stations_v2 = [
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.30, LONGITUD=-58.20,
            ALERTA="8.00"
        )
    ]
    repo.sync_stations(stations_v2)

    result = db_session.query(Station).all()
    assert len(result) == 1
    assert result[0].latitud == -32.30
    assert result[0].alert_value == 8.00


def test_sync_stations_filters_by_river(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", ["URUGUAY"])
    repo = ScraperRepository(db_session)

    stations = [
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        ),
        RawStationData(
            PUERTO="ROSARIO", RIO="PARANA",
            LATITUD=-32.94, LONGITUD=-60.63
        ),
    ]

    repo.sync_stations(stations)

    result = db_session.query(Station).all()
    assert len(result) == 1
    assert result[0].name == "COLON"


def test_sync_stations_dedup_by_name_and_source(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    prefectura_station = RawStationData(
        PUERTO="COLON", RIO="URUGUAY",
        LATITUD=-32.22, LONGITUD=-58.13
    )
    ina_station = RawStationData.model_construct(
        name="COLON", river="URUGUAY", source="ina",
        latitud=-32.22, longitud=-58.13,
        alert_value=None, evacuation_value=None
    )

    repo.sync_stations([prefectura_station])
    repo.sync_stations([ina_station])

    result = db_session.query(Station).all()
    assert len(result) == 2
    sources = {s.source for s in result}
    assert sources == {"prefectura", "ina"}


def test_save_measurements_with_existing_station(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    repo.sync_stations([
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ])

    measurements = [
        RawMeasurementData(
            station_name="COLON",
            source="prefectura",
            date_time=datetime(2026, 2, 14, 12, 0),
            value=2.15,
        )
    ]
    repo.save_measurements(measurements)

    station = db_session.query(Station).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(station_id=station.id).all()
    assert len(mediciones) == 1
    assert mediciones[0].value == 2.15


def test_save_measurements_skips_unknown_station(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    measurements = [
        RawMeasurementData(
            station_name="ESTACION_INEXISTENTE",
            source="prefectura",
            date_time=datetime(2026, 2, 14, 12, 0),
            value=3.50,
        )
    ]
    repo.save_measurements(measurements)

    result = db_session.query(Measurement).all()
    assert len(result) == 0


def test_no_duplicate_measurements(db_session, monkeypatch):
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    repo = ScraperRepository(db_session)

    repo.sync_stations([
        RawStationData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ])

    measurement = [
        RawMeasurementData(
            station_name="COLON",
            source="prefectura",
            date_time=datetime(2026, 2, 14, 12, 0),
            value=2.15,
        )
    ]

    repo.save_measurements(measurement)
    repo.save_measurements(measurement)

    station = db_session.query(Station).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(station_id=station.id).all()
    assert len(mediciones) == 1


# ─── Tests de log_error ───────────────────────────────────────────────────────

from common.models import ScraperError


def test_log_error_persists_record(db_session):
    repo = ScraperRepository(db_session)

    repo.log_error(
        source="INA",
        error_type="HTTP_ERROR",
        error_message="503 Service Unavailable",
        station_name="COLON",
        url="https://alerta.ina.gob.ar/a5/obs/puntual/series/42/observaciones",
        http_status_code=503,
    )

    errors = db_session.query(ScraperError).all()
    assert len(errors) == 1
    err = errors[0]
    assert err.source == "INA"
    assert err.error_type == "HTTP_ERROR"
    assert err.error_message == "503 Service Unavailable"
    assert err.station_name == "COLON"
    assert err.http_status_code == 503
    assert err.url is not None
    assert err.occurred_at is not None


def test_log_error_without_optional_fields(db_session):
    repo = ScraperRepository(db_session)

    repo.log_error(
        source="CARU",
        error_type="TIMEOUT",
        error_message="Read timed out",
    )

    errors = db_session.query(ScraperError).all()
    assert len(errors) == 1
    err = errors[0]
    assert err.station_name is None
    assert err.http_status_code is None
    assert err.url is None


def test_log_error_multiple_records(db_session):
    repo = ScraperRepository(db_session)

    repo.log_error(source="INA", error_type="TIMEOUT", error_message="timeout A", station_name="EST_A")
    repo.log_error(source="INA", error_type="HTTP_ERROR", error_message="500 error", station_name="EST_B", http_status_code=500)
    repo.log_error(source="CARU", error_type="PARSE_ERROR", error_message="bad html")

    errors = db_session.query(ScraperError).all()
    assert len(errors) == 3

    sources = {e.source for e in errors}
    assert sources == {"INA", "CARU"}


def test_log_error_does_not_raise_on_db_failure(db_session, monkeypatch):
    """log_error no debe propagar excepciones aunque falle la DB."""
    repo = ScraperRepository(db_session)

    # Rompemos la sesión para simular falla de DB
    def bad_add(obj):
        raise Exception("DB connection lost")

    monkeypatch.setattr(db_session, "add", bad_add)

    # No debe lanzar
    repo.log_error(source="Prefectura", error_type="UNKNOWN", error_message="algo")
