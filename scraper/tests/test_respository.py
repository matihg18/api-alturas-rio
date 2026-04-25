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
            date_time=datetime(2026, 2, 14, 12, 0),
            value=2.15,
        )
    ]

    repo.save_measurements(measurement)
    repo.save_measurements(measurement)

    station = db_session.query(Station).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(station_id=station.id).all()
    assert len(mediciones) == 1
