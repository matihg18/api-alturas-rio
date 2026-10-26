import logging
from datetime import datetime

import requests

import scraper.config as config
from scraper.openmeteo.strategy import (
    OpenMeteoBackFillStrategy,
    OpenMeteoIncrementalStrategy,
)
from scraper.schemas import PrecipitationPoint, RawPrecipitationData

POINT = PrecipitationPoint(1, "Colón", -32.22, -58.14)


def _row(station_id: int, dt: datetime, value: float = 1.0):
    return RawPrecipitationData(
        station_id=station_id,
        station_name="Colón",
        date_time=dt,
        precipitation=value,
    )


class FakeClient:
    def __init__(self, forecast=None, archive=None, error=None):
        self.forecast = forecast or []
        self.archive = archive or []
        self.error = error
        self.forecast_calls = []
        self.archive_calls = []

    def get_forecast(self, points, past_days):
        self.forecast_calls.append((points, past_days))
        if self.error:
            raise self.error
        return self.forecast

    def get_archive(self, points, start, end):
        self.archive_calls.append((points, start, end))
        if self.error:
            raise self.error
        return self.archive


class SequenceParser:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def parse(self, payloads, points, cutoff=None):
        self.calls.append((payloads, points, cutoff))
        return self.responses.pop(0)


def test_incremental_saves_forecast_and_returns_empty(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_PAST_DAYS", 5)
    now = datetime(2026, 1, 2, 0, 0)
    row = _row(1, datetime(2026, 1, 1, 0, 0))
    saved = []
    parser = SequenceParser([[row]])
    client = FakeClient(forecast=[{"hourly": {}}])

    strategy = OpenMeteoIncrementalStrategy(
        point_provider=lambda: [POINT],
        save_batch=lambda rows: saved.extend(rows) or len(rows),
        client=client,
        parser=parser,
        now_provider=lambda: now,
    )

    assert strategy.get_data() == ([], [])
    assert strategy.persists_internally is True
    assert client.forecast_calls == [([POINT], 5)]
    assert parser.calls[0][2] == now
    assert saved == [row]


def test_incremental_without_points_skips_requests():
    client = FakeClient(forecast=[{"hourly": {}}])
    strategy = OpenMeteoIncrementalStrategy(
        point_provider=lambda: [],
        save_batch=lambda rows: len(rows),
        client=client,
    )

    assert strategy.get_data() == ([], [])
    assert client.forecast_calls == []


def test_incremental_reports_request_error():
    errors = []

    def _on_error(**kwargs):
        errors.append(kwargs)

    strategy = OpenMeteoIncrementalStrategy(
        point_provider=lambda: [POINT],
        save_batch=lambda rows: len(rows),
        client=FakeClient(error=requests.exceptions.Timeout("timeout")),
    )

    assert strategy.get_data(on_error=_on_error) == ([], [])
    assert errors[0]["source"] == "Open-Meteo"
    assert errors[0]["error_type"] == "TIMEOUT"


def test_incremental_reports_save_error():
    errors = []

    def _on_error(**kwargs):
        errors.append(kwargs)

    strategy = OpenMeteoIncrementalStrategy(
        point_provider=lambda: [POINT],
        save_batch=lambda rows: (_ for _ in ()).throw(RuntimeError("db down")),
        client=FakeClient(forecast=[{"hourly": {}}]),
        parser=SequenceParser([[_row(1, datetime(2026, 1, 1))]]),
    )

    assert strategy.get_data(on_error=_on_error) == ([], [])
    assert errors[0]["source"] == "Open-Meteo"
    assert errors[0]["error_type"] == "UNKNOWN"


def test_backfill_fetches_forecast_and_archive_chunks(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_PAST_DAYS", 2)
    monkeypatch.setattr(config, "OPEN_METEO_BACKFILL_CHUNK_DAYS", 10)
    monkeypatch.setattr(config, "OPEN_METEO_ARCHIVE_DELAY_DAYS", 1)

    now = datetime(2026, 1, 31, 12, 0)
    forecast_row = _row(1, datetime(2026, 1, 12, 0, 0))
    archive_row_1 = _row(1, datetime(2026, 1, 15, 0, 0))
    archive_row_2 = _row(1, datetime(2026, 1, 25, 0, 0))
    saved = []
    parser = SequenceParser(
        [[forecast_row], [archive_row_1], [archive_row_2]]
    )
    client = FakeClient(
        forecast=[{"hourly": {}}],
        archive=[{"hourly": {}}, {"hourly": {}}],
    )

    strategy = OpenMeteoBackFillStrategy(
        backfill_days=20,
        point_provider=lambda: [POINT],
        save_batch=lambda rows: saved.extend(rows) or len(rows),
        client=client,
        parser=parser,
        now_provider=lambda: now,
    )

    assert strategy.get_data() == ([], [])
    assert strategy.persists_internally is True
    assert client.forecast_calls == [([POINT], 2)]
    assert len(client.archive_calls) == 2
    assert client.archive_calls[0][1].isoformat() == "2026-01-11"
    assert client.archive_calls[0][2].isoformat() == "2026-01-20"
    assert client.archive_calls[1][1].isoformat() == "2026-01-21"
    assert client.archive_calls[1][2].isoformat() == "2026-01-30"
    assert parser.calls[0][2] == now
    assert parser.calls[1][2] is None
    assert len(saved) == 3


def test_backfill_skips_archive_when_range_is_short(monkeypatch):
    monkeypatch.setattr(config, "OPEN_METEO_PAST_DAYS", 10)

    client = FakeClient(forecast=[{"hourly": {}}])
    strategy = OpenMeteoBackFillStrategy(
        backfill_days=5,
        point_provider=lambda: [POINT],
        save_batch=lambda rows: len(rows),
        client=client,
        parser=SequenceParser([[]]),
    )

    assert strategy.get_data() == ([], [])
    assert client.archive_calls == []


def test_backfill_warns_when_estimate_exceeds_budget(monkeypatch, caplog):
    monkeypatch.setattr(config, "OPEN_METEO_DAILY_CALL_BUDGET", 1)

    strategy = OpenMeteoBackFillStrategy(
        backfill_days=20,
        point_provider=lambda: [POINT],
        save_batch=lambda rows: len(rows),
        client=FakeClient(forecast=[{"hourly": {}}]),
        parser=SequenceParser([[], [], []]),
    )

    with caplog.at_level(logging.WARNING):
        strategy.get_data()

    assert "exceeds budget" in caplog.text
