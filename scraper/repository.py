import logging
from sqlalchemy.orm import Session
from common.models import Port, Measurement
from parser import RawPortData, RawMeasurementData
import config

logger = logging.getLogger(__name__)


class ScraperRepository:
    def __init__(self, session: Session):
        self.db = session

    def sync_ports(self, ports: list[RawPortData]):
        allowed = config.ALLOWED_RIVERS
        count = 0
        for raw_port in ports:
            if allowed and raw_port.river.upper() not in allowed:
                logger.debug(f"SKIPPING PORT {raw_port.name} (RIVER {raw_port.river} NOT ALLOWED)")
                continue
            try:
                port = self.db.query(Port).filter(Port.name == raw_port.name).first()

                if not port:
                    port = Port(
                        name=raw_port.name,
                        river=raw_port.river,
                        latitud=raw_port.latitud,
                        longitud=raw_port.longitud,
                        alert_value=raw_port.alert_value,
                        evacuation_value=raw_port.evacuation_value
                    )
                    self.db.add(port)
                    self.db.flush()
                    logger.info(f"NEW PORT: {port.name}")
                else:
                    port.latitud = raw_port.latitud
                    port.longitud = raw_port.longitud
                    port.alert_value = raw_port.alert_value
                    port.evacuation_value = raw_port.evacuation_value
                    logger.debug(f"UPDATED PORT: {port.name}")

                count += 1
            except Exception as e:
                logger.error(f"ERROR SYNCING PORT {raw_port.name}: {e}")
                self.db.rollback()
                continue

        self.db.commit()
        logger.info(f"PORT SYNC COMPLETED. {count} PORTS PROCESSED.")

    def save_measurements(self, measurements: list[RawMeasurementData]):
        saved = 0
        skipped = 0

        for raw_m in measurements:
            try:
                port = self.db.query(Port).filter(
                    Port.name == raw_m.port_name
                ).first()

                if not port:
                    logger.warning(
                        f"PORT '{raw_m.port_name}' NOT FOUND IN DB, "
                        f"SKIPPING MEASUREMENT ({raw_m.date_time})"
                    )
                    skipped += 1
                    continue

                existing = self.db.query(Measurement).filter(
                    Measurement.port_id == port.id,
                    Measurement.date_time == raw_m.date_time
                ).first()

                if not existing and raw_m.value is not None:
                    new_measurement = Measurement(
                        port_id=port.id,
                        date_time=raw_m.date_time,
                        value=raw_m.value,
                    )
                    self.db.add(new_measurement)
                    saved += 1

            except Exception as e:
                logger.error(f"ERROR SAVING MEASUREMENT FOR {raw_m.port_name}: {e}")
                self.db.rollback()
                continue

        self.db.commit()
        logger.info(
            f"MEASUREMENTS COMPLETED. {saved} SAVED, {skipped} SKIPPED (UNKNOWN PORTS)."
        )
