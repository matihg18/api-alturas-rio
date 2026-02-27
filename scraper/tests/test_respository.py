from datetime import datetime
import config
from repository import ScraperRepository
from parser import RawPortData, RawMeasurementData
from common.models import Port, Measurement


def test_sync_ports_creates_new_port(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    ports = [
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ]

    repo.sync_ports(ports)

    result = db_session.query(Port).all()
    assert len(result) == 1
    assert result[0].name == "COLON"
    assert result[0].latitud == -32.22
    assert result[0].longitud == -58.13


def test_sync_ports_updates_existing_port(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    ports_v1 = [
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13,
            ALERTA="7.10"
        )
    ]
    repo.sync_ports(ports_v1)

    ports_v2 = [
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.30, LONGITUD=-58.20,
            ALERTA="8.00"
        )
    ]
    repo.sync_ports(ports_v2)

    result = db_session.query(Port).all()
    assert len(result) == 1
    assert result[0].latitud == -32.30
    assert result[0].alert_value == 8.00


def test_sync_ports_filters_by_river(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", ["URUGUAY"])
    repo = ScraperRepository(db_session)

    ports = [
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        ),
        RawPortData(
            PUERTO="ROSARIO", RIO="PARANA",
            LATITUD=-32.94, LONGITUD=-60.63
        ),
    ]

    repo.sync_ports(ports)

    result = db_session.query(Port).all()
    assert len(result) == 1
    assert result[0].name == "COLON"


def test_save_measurements_with_existing_port(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    repo.sync_ports([
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ])

    measurements = [
        RawMeasurementData(
            port_name="COLON",
            date_time=datetime(2026, 2, 14, 12, 0),
            value=2.15,
        )
    ]
    repo.save_measurements(measurements)

    puerto = db_session.query(Port).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(port_id=puerto.id).all()
    assert len(mediciones) == 1
    assert mediciones[0].value == 2.15


def test_save_measurements_skips_unknown_port(db_session, monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_RIVERS", [])
    repo = ScraperRepository(db_session)

    measurements = [
        RawMeasurementData(
            port_name="PUERTO_INEXISTENTE",
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

    repo.sync_ports([
        RawPortData(
            PUERTO="COLON", RIO="URUGUAY",
            LATITUD=-32.22, LONGITUD=-58.13
        )
    ])

    measurement = [
        RawMeasurementData(
            port_name="COLON",
            date_time=datetime(2026, 2, 14, 12, 0),
            value=2.15,
        )
    ]

    repo.save_measurements(measurement)
    repo.save_measurements(measurement)

    puerto = db_session.query(Port).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(port_id=puerto.id).all()
    assert len(mediciones) == 1
