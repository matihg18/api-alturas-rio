from datetime import datetime

import pytest

from scraper.openmeteo.parser import OpenMeteoParser
from scraper.schemas import PrecipitationPoint

POINT = PrecipitationPoint(
    station_id=1,
    station_name="Colón",
    latitud=-32.22,
    longitud=-58.14,
)


def test_parse_keeps_zero_and_skips_none():
    payload = {
        "hourly": {
            "time": [
                "2026-01-01T00:00",
                "2026-01-01T01:00",
                "2026-01-01T02:00",
            ],
            "precipitation": [0.0, None, 1.5],
        }
    }

    rows = OpenMeteoParser().parse(payload, [POINT])

    assert len(rows) == 2
    assert rows[0].precipitation == 0.0
    assert rows[1].precipitation == 1.5
    assert rows[0].date_time == datetime(2026, 1, 1, 0, 0)


def test_parse_strips_fixed_offset():
    payload = {
        "hourly": {
            "time": ["2026-01-01T00:00:00-03:00"],
            "precipitation": [0.2],
        }
    }

    rows = OpenMeteoParser().parse(payload, [POINT])

    assert rows[0].date_time == datetime(2026, 1, 1, 0, 0)
    assert rows[0].date_time.tzinfo is None


def test_parse_applies_cutoff():
    payload = {
        "hourly": {
            "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
            "precipitation": [0.0, 0.0],
        }
    }

    rows = OpenMeteoParser().parse(
        payload,
        [POINT],
        cutoff=datetime(2026, 1, 1, 0, 0),
    )

    assert len(rows) == 1
    assert rows[0].date_time == datetime(2026, 1, 1, 0, 0)


def test_parse_multiple_points():
    payloads = [
        {
            "hourly": {
                "time": ["2026-01-01T00:00"],
                "precipitation": [1.0],
            }
        },
        {
            "hourly": {
                "time": ["2026-01-01T00:00"],
                "precipitation": [2.0],
            }
        },
    ]
    points = [
        POINT,
        PrecipitationPoint(2, "Concordia", -31.39, -58.02),
    ]

    rows = OpenMeteoParser().parse(payloads, points)

    assert [row.station_id for row in rows] == [1, 2]
    assert [row.precipitation for row in rows] == [1.0, 2.0]


def test_parse_payload_count_mismatch_raises():
    with pytest.raises(ValueError):
        OpenMeteoParser().parse([], [POINT])


def test_parse_time_value_length_mismatch_raises():
    payload = {
        "hourly": {
            "time": ["2026-01-01T00:00"],
            "precipitation": [1.0, 2.0],
        }
    }

    with pytest.raises(ValueError):
        OpenMeteoParser().parse(payload, [POINT])
