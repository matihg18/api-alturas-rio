import logging
import os
from sqlalchemy.orm import Session
from common.models import Port, Measurement
from parser import RawPortData

logger = logging.getLogger(__name__)

class ScraperRepository:
    def __init__(self, session: Session):
        self.db = session
        allowed_raw = os.getenv("ALLOWED_RIVERS", "")
        self.allowed_rivers = [r.strip().upper() for r in allowed_raw.split(",")] if allowed_raw else []

    def save_all(self, parsed_ports: list[RawPortData]):
        count = 0
        for raw_port in parsed_ports:
            if self.allowed_rivers and raw_port.river.upper() not in self.allowed_rivers:
                logger.debug(f"SKIPPING PORT {raw_port.name} (RIVER {raw_port.river} NOT ALLOWED)")
                continue
            
            try:
                self._process_single_port(raw_port)
                count += 1
            except Exception as e:
                logger.error(f"ERROR PROCESSING PORT {raw_port.name}: {e}")
                self.db.rollback()
                continue
        
        self.db.commit()
        logger.info(f"PROCESS COMPLETED. {count} HAVE BEEN SAVED.")

    def _process_single_port(self, raw: RawPortData):
        port = self.db.query(Port).filter(Port.name == raw.name).first()

        if not port:
            port = Port(
                name=raw.name,
                river=raw.river,
                latitud=raw.latitud,
                longitud=raw.longitud,
                alert_value=raw.alert_value,
                evacuation_value=raw.evacuacion_value
            )
            self.db.add(port)
            self.db.flush() 
            logger.info(f"NEW PORT: {port.name}")
        else:
            port.latitud = raw.latitud
            port.longitud = raw.longitud
            port.alert_value = raw.alert_value
            port.evacuation_value = raw.evacuacion_value
            logger.debug(f"UPDATED PORT: {port.name}")

        timestamp = raw.timestamp

        existing_m = self.db.query(Measurement).filter(
            Measurement.port_id == port.id,
            Measurement.date_time == timestamp
        ).first()

        if not existing_m and raw.value is not None:
            new_measurement = Measurement(
                port_id=port.id,
                date_time=timestamp,
                value=raw.value,
                state=raw.state,
                delta=raw.delta if raw.delta is not None else 0.0
            )
            self.db.add(new_measurement)
            logger.info(f"SAVED MEASUREMENT TO {port.name}: {raw.value}m")