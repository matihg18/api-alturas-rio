import logging
from datetime import datetime
from typing import Optional

from scraper.schemas import PrecipitationPoint, RawPrecipitationData

logger = logging.getLogger(__name__)


class OpenMeteoParser:
    def parse(
        self,
        payloads: list[dict] | dict,
        points: list[PrecipitationPoint],
        cutoff: Optional[datetime] = None,
    ) -> list[RawPrecipitationData]:
        if not isinstance(payloads, list):
            payloads = [payloads]

        if len(payloads) != len(points):
            raise ValueError(
                f"Open-Meteo returned {len(payloads)} payloads for "
                f"{len(points)} points"
            )

        rows: list[RawPrecipitationData] = []
        for point, payload in zip(points, payloads):
            hourly = payload.get("hourly") or {}
            times = hourly.get("time") or []
            values = hourly.get("precipitation") or []

            if len(times) != len(values):
                raise ValueError(
                    f"Open-Meteo time/precipitation length mismatch for "
                    f"station {point.station_id}"
                )

            for raw_time, value in zip(times, values):
                if value is None:
                    continue
                dt = self._parse_time(raw_time)
                if cutoff is not None and dt > cutoff:
                    continue
                rows.append(
                    RawPrecipitationData(
                        station_id=point.station_id,
                        station_name=point.station_name,
                        date_time=dt,
                        precipitation=float(value),
                    )
                )
        return rows

    @staticmethod
    def _parse_time(value: str) -> datetime:
        """Convierte el timestamp ISO de Open-Meteo a datetime local naive.

        Open-Meteo devuelve ISO 8601 con el offset fijo de la timezone pedida.
        Al quitar tzinfo conservamos la hora local de pared (Argentina no usa DST).
        """
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
