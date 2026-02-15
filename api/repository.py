from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from common.models import Measurement

class ApiRepository:
    def __init__(self, session: Session):
        self.db_session = session

    def get_measurements_by_port_id(self, port_id: int):
        stmt = (
           select(Measurement)
            .where(Measurement.port_id == port_id)
            .order_by(desc(Measurement.date_time))
        )
        result = self.db_session.execute(stmt)
        return result.scalars().all()