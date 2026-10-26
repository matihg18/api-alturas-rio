from datetime import date
from unittest.mock import MagicMock

import pytest
import requests

import scraper.config as config
from scraper.openmeteo.client import OpenMeteoClient
from scraper.schemas import PrecipitationPoint

POINTS = [
    PrecipitationPoint(1, "Colón", -32.22, -58.14),
    PrecipitationPoint(2, "Concordia", -31.39, -58.02),
]


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._data


def test_get_forecast_batches_points(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_MAX_POINTS_PER_REQUEST", 1)
    session = MagicMock()
    session.get.side_effect = [
        FakeResponse({"hourly": {}}),
        FakeResponse({"hourly": {}}),
    ]
    client = OpenMeteoClient(session=session)

    result = client.get_forecast(POINTS, past_days=10)

    assert len(result) == 2
    assert session.get.call_count == 2
    first_params = session.get.call_args_list[0].kwargs["params"]
    assert first_params["latitude"] == "-32.22"
    assert first_params["longitude"] == "-58.14"
    assert first_params["hourly"] == "precipitation"
    assert first_params["precipitation_unit"] == "mm"
    assert first_params["past_days"] == 10
    assert first_params["forecast_days"] == 1


def test_get_archive_sends_dates_and_model(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_MAX_POINTS_PER_REQUEST", 50)
    monkeypatch.setattr(config, "OPEN_METEO_ARCHIVE_MODEL", "era5")
    session = MagicMock()
    session.get.return_value = FakeResponse({"hourly": {}})
    client = OpenMeteoClient(session=session)

    result = client.get_archive(
        POINTS,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
    )

    assert result == [{"hourly": {}}]
    params = session.get.call_args.kwargs["params"]
    assert params["start_date"] == "2026-01-01"
    assert params["end_date"] == "2026-01-10"
    assert params["models"] == "era5"


def test_client_includes_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_API_KEY", "secret")
    session = MagicMock()
    session.get.return_value = FakeResponse({"hourly": {}})
    client = OpenMeteoClient(session=session)

    client.get_forecast([POINTS[0]], past_days=1)

    params = session.get.call_args.kwargs["params"]
    assert params["apikey"] == "secret"


def test_client_raises_on_error_payload():
    session = MagicMock()
    session.get.return_value = FakeResponse(
        {"error": True, "reason": "bad request"}
    )
    client = OpenMeteoClient(session=session)

    with pytest.raises(ValueError, match="bad request"):
        client.get_forecast([POINTS[0]], past_days=1)


def test_client_raises_on_http_error():
    session = MagicMock()
    session.get.return_value = FakeResponse({}, status_code=500)
    client = OpenMeteoClient(session=session)

    with pytest.raises(requests.HTTPError):
        client.get_forecast([POINTS[0]], past_days=1)
