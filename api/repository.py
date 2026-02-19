from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from common.models import Measurement, Port
from datetime import date


class ApiRepository:
    def __init__(self, session: Session):
        self.db_session = session

    def get_port_list(self):
        stmt = (
            select(Port)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().all()

    def get_port_by_port_id(self, port_id: int):
        stmt = (
            select(Port)
            .where(Port.id == port_id)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().first()

    def get_ports_with_height_alert(self):
        stmt = (
            select(Port)
            .join(Measurement)
            .where(Measurement.value > Port.alert_value)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().all()

    def get_ports_with_evacutation_alert(self):
        stmt = (
            select(Port)
            .join(Measurement)
            .where(Measurement.value > Port.evacuation_value)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().all()

    def get_measurements_by_port_id(self, port_id: int, from_date: date, to_date: date):
        stmt = select(Measurement).where(Measurement.port_id == port_id)
        if from_date:
            stmt = stmt.where(func.date(Measurement.date_time) >= from_date)
        if to_date:
            stmt = stmt.where(func.date(Measurement.date_time) <= to_date)
        stmt = stmt.order_by(desc(Measurement.date_time))
        result = self.db_session.execute(stmt)
        return result.scalars().all()

    def get_latest_measurement_by_port_id(self, port_id: int):
        stmt = (
            select(Measurement)
            .where(Measurement.port_id == port_id)
            .order_by(desc(Measurement.date_time))
            .limit(1)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().first()
