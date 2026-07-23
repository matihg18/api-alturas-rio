import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from common.models import Station, Measurement, ScraperError
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)


class ScraperRepository:
    def __init__(self, session: Session):
        self.db = session

    def sync_stations(self, stations: list[RawStationData]):
        count = 0
        for raw_station in stations:
            try:
                station = (
                    self.db.query(Station)
                    .filter(
                        Station.name == raw_station.name,
                        Station.source == raw_station.source,
                    )
                    .first()
                )

                if not station:
                    station = Station(
                        name=raw_station.name,
                        river=raw_station.river,
                        source=raw_station.source,
                        latitud=raw_station.latitud,
                        longitud=raw_station.longitud,
                        alert_value=raw_station.alert_value,
                        evacuation_value=raw_station.evacuation_value,
                    )
                    self.db.add(station)
                    self.db.flush()
                    logger.info(f"NEW STATION: {station.name} ({station.source})")
                else:
                    station.latitud = raw_station.latitud
                    station.longitud = raw_station.longitud
                    station.alert_value = raw_station.alert_value
                    station.evacuation_value = raw_station.evacuation_value
                    logger.debug(f"UPDATED STATION: {station.name} ({station.source})")

                count += 1
            except Exception as e:
                logger.error(f"ERROR SYNCING STATION {raw_station.name}: {e}")
                self.db.rollback()
                continue

        self.db.commit()
        logger.info(f"STATION SYNC COMPLETED. {count} STATIONS PROCESSED.")

    def save_measurements(self, measurements: list[RawMeasurementData]):
        saved = 0
        skipped = 0

        for raw_m in measurements:
            try:
                station = (
                    self.db.query(Station)
                    .filter(Station.name == raw_m.station_name, Station.source == raw_m.source)
                    .first()
                )

                if not station:
                    logger.warning(
                        f"STATION '{raw_m.station_name}' NOT FOUND IN DB, "
                        f"SKIPPING MEASUREMENT ({raw_m.date_time})"
                    )
                    skipped += 1
                    continue

                existing = self.db.query(Measurement).filter(
                    Measurement.station_id == station.id,
                    Measurement.date_time == raw_m.date_time
                ).first()

                if not existing and raw_m.value is not None:
                    new_measurement = Measurement(
                        station_id=station.id,
                        date_time=raw_m.date_time,
                        value=raw_m.value,
                    )
                    self.db.add(new_measurement)
                    saved += 1

            except Exception as e:
                logger.error(f"ERROR SAVING MEASUREMENT FOR {raw_m.station_name}: {e}")
                self.db.rollback()
                continue

        self.db.commit()
        logger.info(
            f"MEASUREMENTS COMPLETED. {saved} SAVED, {skipped} SKIPPED (UNKNOWN STATIONS)."
        )

    def log_error(
        self,
        source: str,
        error_type: str,
        error_message: str,
        station_name: Optional[str] = None,
        url: Optional[str] = None,
        http_status_code: Optional[int] = None,
    ) -> None:
        try:
            record = ScraperError(
                source=source,
                station_name=station_name,
                error_type=error_type,
                http_status_code=http_status_code,
                url=url,
                error_message=str(error_message),
                occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            self.db.add(record)
            self.db.commit()
        except Exception as e:
            logger.error(f"FAILED TO LOG SCRAPER ERROR TO DB: {e}")
            self.db.rollback()
