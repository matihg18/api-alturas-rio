import logging
from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from scraper.base import OnErrorCallback, ScraperStrategy
from scraper.errors import classify_error
from scraper.openmeteo.client import OpenMeteoClient
from scraper.openmeteo.parser import OpenMeteoParser
from scraper.schemas import (
    PrecipitationPoint,
    RawMeasurementData,
    RawPrecipitationData,
    RawStationData,
)
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "Open-Meteo"

PointProvider = Callable[[], list[PrecipitationPoint]]
SaveBatch = Callable[[list[RawPrecipitationData]], int]


def _local_now() -> datetime:
    try:
        return datetime.now(ZoneInfo(config.OPEN_METEO_TIMEZONE)).replace(tzinfo=None)
    except Exception:
        return datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)


def _date_chunks(
    start: date,
    end: date,
    chunk_days: int,
) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _estimate_calls(points: int, days: int) -> int:
    """Estimación conservadora: Open-Meteo cuenta ~1 llamada por 14 días/ubicación."""
    if points <= 0 or days <= 0:
        return 0
    return ceil(points * days / 14)


class _OpenMeteoBase(ScraperStrategy):
    persists_internally = True

    def __init__(
        self,
        point_provider: PointProvider,
        save_batch: SaveBatch,
        client: Optional[OpenMeteoClient] = None,
        parser: Optional[OpenMeteoParser] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
    ):
        self.point_provider = point_provider
        self.save_batch = save_batch
        self.client = client or OpenMeteoClient()
        self.parser = parser or OpenMeteoParser()
        self.now_provider = now_provider or _local_now

    def _get_points(self) -> list[PrecipitationPoint]:
        points = self.point_provider()
        if not points:
            logger.info("Open-Meteo: no hay estaciones habilitadas con coordenadas.")
        return points

    def _save(
        self,
        rows: list[RawPrecipitationData],
        on_error: OnErrorCallback,
        context: str,
    ) -> int:
        if not rows:
            return 0
        try:
            saved = self.save_batch(rows)
            logger.info(f"Open-Meteo: {saved} measurements saved ({context}).")
            return saved
        except Exception as e:
            logger.error(f"Open-Meteo: error saving {context}: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=None,
                    http_status_code=status,
                )
            return 0

    def _fetch_forecast(
        self,
        points: list[PrecipitationPoint],
        past_days: int,
        cutoff: datetime,
        on_error: OnErrorCallback,
    ) -> list[RawPrecipitationData]:
        try:
            payloads = self.client.get_forecast(points, past_days)
            return self.parser.parse(payloads, points, cutoff=cutoff)
        except Exception as e:
            logger.error(f"Open-Meteo: forecast request failed: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=config.OPEN_METEO_FORECAST_URL,
                    http_status_code=status,
                )
            return []

    def _fetch_archive(
        self,
        points: list[PrecipitationPoint],
        start: date,
        end: date,
        on_error: OnErrorCallback,
    ) -> list[RawPrecipitationData]:
        try:
            payloads = self.client.get_archive(points, start, end)
            return self.parser.parse(payloads, points)
        except Exception as e:
            logger.error(f"Open-Meteo: archive request failed [{start} -> {end}]: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=config.OPEN_METEO_ARCHIVE_URL,
                    http_status_code=status,
                )
            return []


class OpenMeteoIncrementalStrategy(_OpenMeteoBase):
    def __init__(
        self,
        point_provider: PointProvider,
        save_batch: SaveBatch,
        past_days: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(point_provider, save_batch, **kwargs)
        self.past_days = past_days or config.OPEN_METEO_PAST_DAYS

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> tuple[list[RawStationData], list[RawMeasurementData]]:
        points = self._get_points()
        if not points:
            return [], []

        now = self.now_provider()
        rows = self._fetch_forecast(points, self.past_days, now, on_error)
        self._save(rows, on_error, "incremental forecast")
        return [], []


class OpenMeteoBackFillStrategy(_OpenMeteoBase):
    def __init__(
        self,
        backfill_days: int,
        point_provider: PointProvider,
        save_batch: SaveBatch,
        **kwargs,
    ):
        super().__init__(point_provider, save_batch, **kwargs)
        self.backfill_days = max(1, backfill_days)
        self.past_days = min(config.OPEN_METEO_PAST_DAYS, self.backfill_days)
        self.chunk_days = config.OPEN_METEO_BACKFILL_CHUNK_DAYS
        self.archive_delay_days = config.OPEN_METEO_ARCHIVE_DELAY_DAYS

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> tuple[list[RawStationData], list[RawMeasurementData]]:
        points = self._get_points()
        if not points:
            return [], []

        now = self.now_provider()
        total_start = now - timedelta(days=self.backfill_days)

        estimated_calls = _estimate_calls(len(points), self.backfill_days)
        if estimated_calls > config.OPEN_METEO_DAILY_CALL_BUDGET:
            logger.warning(
                f"Open-Meteo backfill: estimated {estimated_calls} calls exceeds "
                f"budget {config.OPEN_METEO_DAILY_CALL_BUDGET}. Reduce "
                f"BACKFILL_DAYS or the number of enabled stations."
            )

        total_saved = 0

        recent_rows = self._fetch_forecast(
            points, self.past_days, now, on_error
        )
        recent_rows = [
            row for row in recent_rows if row.date_time >= total_start
        ]
        total_saved += self._save(recent_rows, on_error, "recent forecast")

        if self.backfill_days > self.past_days:
            archive_start = total_start.date()
            archive_end = (
                now - timedelta(days=self.archive_delay_days)
            ).date()
            if archive_start < date(1940, 1, 1):
                archive_start = date(1940, 1, 1)

            if archive_start <= archive_end:
                chunks = _date_chunks(
                    archive_start, archive_end, self.chunk_days
                )
                logger.info(
                    f"Open-Meteo backfill: {len(chunks)} archive chunk(s) "
                    f"from {archive_start} to {archive_end}"
                )
                for start, end in chunks:
                    rows = self._fetch_archive(points, start, end, on_error)
                    total_saved += self._save(
                        rows, on_error, f"archive {start} -> {end}"
                    )
            else:
                logger.info("Open-Meteo backfill: no archive range needed.")

        logger.info(
            f"Open-Meteo backfill: {total_saved} precipitation measurements saved."
        )
        return [], []
