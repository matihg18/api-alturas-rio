import pytest
from datetime import datetime
from scraper.ina.parser import INAParser
from scraper.schemas import RawStationData, RawMeasurementData


@pytest.fixture
def sample_series():
    return [
        {
            "id": 26,
            "tipo": "puntual",
            "estacion": {
                "id": 26,
                "nombre": "La Paz",
                "rio": "PARANAINF",
                "geom": {
                    "type": "Point",
                    "coordinates": [-59.638, -30.734]
                },
                "nivel_alerta": 5.8,
                "nivel_evacuacion": 6.15,
            },
            "var": {"id": 2, "nombre": "Altura hidrométrica"},
        },
        {
            "id": 100,
            "tipo": "puntual",
            "estacion": {
                "id": 100,
                "nombre": "Concordia",
                "rio": "URUGUAY",
                "geom": {
                    "type": "Point",
                    "coordinates": [-58.02, -31.39]
                },
                "nivel_alerta": 10.5,
                "nivel_evacuacion": 13.5,
            },
            "var": {"id": 2, "nombre": "Altura hidrométrica"},
        },
        {
            "id": 200,
            "tipo": "puntual",
            "estacion": {
                "id": 200,
                "nombre": "Sin coordenadas",
                "rio": "URUGUAY",
                "geom": None,
                "nivel_alerta": None,
                "nivel_evacuacion": None,
            },
            "var": {"id": 2, "nombre": "Altura hidrométrica"},
        },
    ]


@pytest.fixture
def sample_observations():
    return [
        {
            "id": 1001,
            "series_id": 26,
            "timestart": "2026-04-18T03:00:00.000Z",
            "timeend": "2026-04-18T03:00:00.000Z",
            "valor": 3.27,
        },
        {
            "id": 1002,
            "series_id": 26,
            "timestart": "2026-04-19T03:00:00.000Z",
            "timeend": "2026-04-19T03:00:00.000Z",
            "valor": 3.15,
        },
        {
            "id": 1003,
            "series_id": 26,
            "timestart": "2026-04-20T03:00:00.000Z",
            "timeend": "2026-04-20T03:00:00.000Z",
            "valor": None,  # debe ser ignorado
        },
    ]


def test_parse_series_returns_station_data(sample_series):
    parser = INAParser()
    stations = parser.parse_series(sample_series)

    # La estación sin coordenadas debe ser ignorada
    assert len(stations) == 2
    assert all(isinstance(s, RawStationData) for s in stations)


def test_parse_series_source_is_ina(sample_series):
    parser = INAParser()
    stations = parser.parse_series(sample_series)
    assert all(s.source == "ina" for s in stations)


def test_parse_series_correct_fields(sample_series):
    parser = INAParser()
    stations = parser.parse_series(sample_series)

    concordia = next(s for s in stations if s.name == "Concordia")
    assert concordia.river == "URUGUAY"
    assert concordia.latitud == pytest.approx(-31.39)
    assert concordia.longitud == pytest.approx(-58.02)
    assert concordia.alert_value == 10.5
    assert concordia.evacuation_value == 13.5


def test_parse_series_deduplicates_stations():
    parser = INAParser()
    duplicated = [
        {
            "id": 1,
            "estacion": {
                "nombre": "Duplicada",
                "rio": "URUGUAY",
                "geom": {"coordinates": [-58.0, -31.0]},
                "nivel_alerta": None,
                "nivel_evacuacion": None,
            }
        },
        {
            "id": 2,
            "estacion": {
                "nombre": "Duplicada",
                "rio": "URUGUAY",
                "geom": {"coordinates": [-58.0, -31.0]},
                "nivel_alerta": None,
                "nivel_evacuacion": None,
            }
        },
    ]
    stations = parser.parse_series(duplicated)
    assert len(stations) == 1


def test_parse_observations_returns_measurements(sample_observations):
    parser = INAParser()
    measurements = parser.parse_observations(sample_observations, "La Paz")

    # La observación con valor=None debe ser ignorada
    assert len(measurements) == 2
    assert all(isinstance(m, RawMeasurementData) for m in measurements)


def test_parse_observations_correct_fields(sample_observations):
    parser = INAParser()
    measurements = parser.parse_observations(sample_observations, "La Paz")

    assert measurements[0].station_name == "La Paz"
    assert measurements[0].value == 3.27
    expected_dt = datetime.fromisoformat("2026-04-18T03:00:00.000+00:00").astimezone().replace(tzinfo=None)
    assert measurements[0].date_time == expected_dt


def test_parse_observations_ignores_null_valor(sample_observations):
    parser = INAParser()
    measurements = parser.parse_observations(sample_observations, "La Paz")

    values = [m.value for m in measurements]
    assert None not in values
