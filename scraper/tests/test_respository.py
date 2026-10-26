from datetime import datetime
from unittest.mock import MagicMock
from scraper.context import ScraperContext
from scraper.repository import ScraperRepository
from scraper.schemas import (
    PrecipitationPoint,
    RawMeasurementData,
    RawPrecipitationData,
    RawStationData,
)
from common.models import Station, Measurement, PrecipitationMeasurement
from common.models import ScraperError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_station(name: str, river: str, source: str = "prefectura") -> RawStationData:
    return RawStationData(name=name, river=river, source=source)


# ---------------------------------------------------------------------------
# Tests de ScraperContext — filtrado por río
# ---------------------------------------------------------------------------

def test_context_filter_stations_no_filter():
    """Con allowed_rivers vacío, todas las estaciones pasan."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=[],
    )
    stations = [
        _make_station("COLON", "URUGUAY"),
        _make_station("ROSARIO", "PARANA"),
    ]
    assert ctx._filter_stations(stations) == stations


def test_context_filter_stations_single_river():
    """Solo pasan las estaciones del río permitido."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["URUGUAY"],
    )
    stations = [
        _make_station("COLON", "URUGUAY"),
        _make_station("ROSARIO", "PARANA"),
    ]
    result = ctx._filter_stations(stations)
    assert len(result) == 1
    assert result[0].name == "COLON"


def test_context_filter_stations_multiple_rivers():
    """Pasan estaciones de todos los ríos en la lista."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["URUGUAY", "GUALEGUAYCHU"],
    )
    stations = [
        _make_station("COLON", "URUGUAY"),
        _make_station("ROSARIO", "PARANA"),
        _make_station("Puerto Local", "GUALEGUAYCHU", source="municipalidad_gchu"),
    ]
    result = ctx._filter_stations(stations)
    assert len(result) == 2
    names = {s.name for s in result}
    assert names == {"COLON", "Puerto Local"}


def test_context_filter_stations_case_insensitive():
    """El filtro es insensible a mayúsculas/minúsculas."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["uruguay"],
    )
    stations = [_make_station("COLON", "URUGUAY")]
    assert len(ctx._filter_stations(stations)) == 1


def test_context_filter_stations_diacritic_normalization():
    """El filtro ignora acentos: 'PARANA' matchea con 'Paraná' y viceversa."""
    # Caso 1: .env sin acento, fuente con acento
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["PARANA"],
    )
    assert len(ctx._filter_stations([_make_station("ROSARIO", "Paraná")])) == 1

    # Caso 2: .env con acento, fuente sin acento
    ctx2 = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["PARANÁ"],
    )
    assert len(ctx2._filter_stations([_make_station("ROSARIO", "PARANA")])) == 1

    # Caso 3: ambos con acento
    assert len(ctx2._filter_stations([_make_station("ROSARIO", "Paraná")])) == 1


def test_context_filter_stations_ina_subdivisions():
    """PARANA matchea con subdivisiones concatenadas de INA como PARANAMED, PARANAINF, etc."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["PARANA"],
    )
    stations = [
        _make_station("Ituzaingó", "PARANAMED", source="ina"),
        _make_station("Rosario", "PARANAINF", source="ina"),
        _make_station("Zárate", "PARANADELASPALMAS", source="ina"),
        _make_station("San Javier", "SANJAVIER", source="ina"),
    ]
    filtered = ctx._filter_stations(stations)
    assert len(filtered) == 3
    names = {s.name for s in filtered}
    assert names == {"Ituzaingó", "Rosario", "Zárate"}


def test_context_filter_unrelated_river_not_present():
    """Un río en allowed_rivers que ninguna estación reporta no causa errores."""
    ctx = ScraperContext(
        strategy=MagicMock(),
        station_syncer=MagicMock(),
        repository=MagicMock(),
        allowed_rivers=["MOCORETA"],
    )
    stations = [
        _make_station("COLON", "URUGUAY"),
        _make_station("ROSARIO", "PARANA"),
    ]
    assert ctx._filter_stations(stations) == []


# ---------------------------------------------------------------------------
# Tests de ScraperRepository — persistencia
# ---------------------------------------------------------------------------

def test_sync_stations_creates_new_station(db_session):
    repo = ScraperRepository(db_session)

    repo.sync_stations([_make_station("COLON", "URUGUAY")])

    result = db_session.query(Station).all()
    assert len(result) == 1
    assert result[0].name == "COLON"


def test_sync_stations_updates_existing_station(db_session):
    repo = ScraperRepository(db_session)

    repo.sync_stations([RawStationData(
        name="COLON", river="URUGUAY", source="prefectura",
        latitud=-32.22, longitud=-58.13, alert_value=7.10,
    )])
    repo.sync_stations([RawStationData(
        name="COLON", river="URUGUAY", source="prefectura",
        latitud=-32.30, longitud=-58.20, alert_value=8.00,
    )])

    result = db_session.query(Station).all()
    assert len(result) == 1
    assert result[0].latitud == -32.30
    assert result[0].alert_value == 8.00


def test_sync_stations_accepts_all_rivers_without_filter(db_session):
    """El repositorio persiste todo lo que recibe — el filtrado es responsabilidad del llamador."""
    repo = ScraperRepository(db_session)

    repo.sync_stations([
        _make_station("COLON", "URUGUAY"),
        _make_station("ROSARIO", "PARANA"),
    ])

    result = db_session.query(Station).all()
    assert len(result) == 2


def test_sync_stations_dedup_by_name_and_source(db_session):
    repo = ScraperRepository(db_session)

    repo.sync_stations([_make_station("COLON", "URUGUAY", source="prefectura")])
    repo.sync_stations([_make_station("COLON", "URUGUAY", source="ina")])

    result = db_session.query(Station).all()
    assert len(result) == 2
    sources = {s.source for s in result}
    assert sources == {"prefectura", "ina"}


def test_save_measurements_with_existing_station(db_session):
    repo = ScraperRepository(db_session)

    repo.sync_stations([_make_station("COLON", "URUGUAY")])

    repo.save_measurements([RawMeasurementData(
        station_name="COLON",
        source="prefectura",
        date_time=datetime(2026, 2, 14, 12, 0),
        value=2.15,
    )])

    station = db_session.query(Station).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(station_id=station.id).all()
    assert len(mediciones) == 1
    assert mediciones[0].value == 2.15


def test_save_measurements_skips_unknown_station(db_session):
    repo = ScraperRepository(db_session)

    repo.save_measurements([RawMeasurementData(
        station_name="ESTACION_INEXISTENTE",
        source="prefectura",
        date_time=datetime(2026, 2, 14, 12, 0),
        value=3.50,
    )])

    result = db_session.query(Measurement).all()
    assert len(result) == 0


def test_no_duplicate_measurements(db_session):
    repo = ScraperRepository(db_session)

    repo.sync_stations([_make_station("COLON", "URUGUAY")])

    measurement = [RawMeasurementData(
        station_name="COLON",
        source="prefectura",
        date_time=datetime(2026, 2, 14, 12, 0),
        value=2.15,
    )]

    repo.save_measurements(measurement)
    repo.save_measurements(measurement)

    station = db_session.query(Station).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(station_id=station.id).all()
    assert len(mediciones) == 1


# ─── Tests de log_error ───────────────────────────────────────────────────────


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
    repo.log_error(
        source="INA",
        error_type="HTTP_ERROR",
        error_message="500 error",
        station_name="EST_B", http_status_code=500
    )
    repo.log_error(source="CARU", error_type="PARSE_ERROR", error_message="bad html")

    errors = db_session.query(ScraperError).all()
    assert len(errors) == 3

    sources = {e.source for e in errors}
    assert sources == {"INA", "CARU"}


def test_log_error_does_not_raise_on_db_failure(db_session, monkeypatch):
    """log_error no debe propagar excepciones aunque falle la DB."""
    repo = ScraperRepository(db_session)

    def bad_add(obj):
        raise Exception("DB connection lost")

    monkeypatch.setattr(db_session, "add", bad_add)

    # No debe lanzar
    repo.log_error(source="Prefectura", error_type="UNKNOWN", error_message="algo")


# ---------------------------------------------------------------------------
# Tests de precipitación
# ---------------------------------------------------------------------------

def test_get_precipitation_points_filters_enabled_and_coordinates(db_session):
    enabled = Station(
        name="A",
        river="URUGUAY",
        source="test",
        latitud=-32.0,
        longitud=-58.0,
        precipitation_enabled=True,
    )
    disabled = Station(
        name="B",
        river="URUGUAY",
        source="test",
        latitud=-33.0,
        longitud=-59.0,
        precipitation_enabled=False,
    )
    no_coords = Station(
        name="C",
        river="URUGUAY",
        source="test",
        latitud=None,
        longitud=None,
        precipitation_enabled=True,
    )
    db_session.add_all([enabled, disabled, no_coords])
    db_session.commit()

    points = ScraperRepository(db_session).get_precipitation_points()

    assert points == [
        PrecipitationPoint(
            station_id=enabled.id,
            station_name="A",
            latitud=-32.0,
            longitud=-58.0,
        )
    ]


def test_save_precipitation_measurements_dedupes_and_keeps_zero(db_session):
    station = Station(
        name="A",
        river="URUGUAY",
        source="test",
        latitud=-32.0,
        longitud=-58.0,
        precipitation_enabled=True,
    )
    db_session.add(station)
    db_session.commit()
    repo = ScraperRepository(db_session)

    rows = [
        RawPrecipitationData(
            station_id=station.id,
            station_name="A",
            date_time=datetime(2026, 1, 1, 0, 0),
            precipitation=0.0,
        ),
        RawPrecipitationData(
            station_id=station.id,
            station_name="A",
            date_time=datetime(2026, 1, 1, 0, 0),
            precipitation=5.0,
        ),
        RawPrecipitationData(
            station_id=station.id,
            station_name="A",
            date_time=datetime(2026, 1, 1, 1, 0),
            precipitation=2.0,
        ),
    ]

    assert repo.save_precipitation_measurements(rows) == 2

    saved = (
        db_session.query(PrecipitationMeasurement)
        .order_by(PrecipitationMeasurement.date_time)
        .all()
    )
    assert len(saved) == 2
    assert saved[0].precipitation == 0.0
    assert saved[1].precipitation == 2.0

    assert repo.save_precipitation_measurements(rows) == 0


def test_save_precipitation_measurements_empty_returns_zero(db_session):
    repo = ScraperRepository(db_session)

    assert repo.save_precipitation_measurements([]) == 0


def test_context_skips_generic_save_when_strategy_persists_internally():
    strategy = MagicMock()
    strategy.persists_internally = True
    strategy.get_data.return_value = ([], [])
    syncer = MagicMock()
    syncer.sync.return_value = []
    repo = MagicMock()

    ScraperContext(
        strategy=strategy,
        station_syncer=syncer,
        repository=repo,
    ).execute()

    repo.save_measurements.assert_not_called()


def test_context_saves_generic_measurements_when_strategy_does_not_persist():
    strategy = MagicMock()
    strategy.persists_internally = False
    strategy.get_data.return_value = ([], [])
    syncer = MagicMock()
    syncer.sync.return_value = []
    repo = MagicMock()

    ScraperContext(
        strategy=strategy,
        station_syncer=syncer,
        repository=repo,
    ).execute()

    repo.save_measurements.assert_called_once_with([])
