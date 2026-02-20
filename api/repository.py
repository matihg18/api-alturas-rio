from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from common.models import Measurement, Port
from datetime import date
from api.schemas import PagedResultResponse, PagingParams, DateFilters


class ApiRepository:
    def __init__(self, session: Session):
        self.db_session = session

    def _apply_paging_and_sorting(self, stmt, model, paging: PagingParams):
        if paging.sorting:
            try:
                parts = paging.sorting.split("-")
                col_name = parts[0]
                direction = parts[1].lower() if len(parts) > 1 else "asc"
                col_attr = getattr(model, col_name)
                
                if direction == "desc":
                    stmt = stmt.order_by(desc(col_attr))
                else:
                    stmt = stmt.order_by(asc(col_attr))
            except (AttributeError, IndexError):
                pass
        
        return stmt.offset(paging.skip).limit(paging.limit)

    def get_port_list(self, paging: PagingParams):
        base_stmt = (select(Port))
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Measurement, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        result = PagedResultResponse(total_count = total_count, items = items)
        return result

    def get_port_by_port_id(self, port_id: int):
        stmt = (
            select(Port)
            .where(Port.id == port_id)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().first()

    def get_ports_with_height_alert(self, paging: PagingParams):
        base_stmt = (
            select(Port)
            .join(Measurement)
            .where(Measurement.value > Port.alert_value)
        )
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Measurement, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        result = PagedResultResponse(total_count = total_count, items = items)
        return result

    def get_ports_with_evacutation_alert(self, paging: PagingParams):
        base_stmt = (
            select(Port)
            .join(Measurement)
            .where(Measurement.value > Port.evacuation_value)
        )
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Measurement, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        result = PagedResultResponse(total_count = total_count, items = items)
        return result

    def get_measurements_by_port_id(
        self,
        port_id: int,
        paging: PagingParams,
        date_filters: DateFilters
    ):
        base_stmt = select(Measurement).where(Measurement.port_id == port_id)
        if date_filters.from_date:
            base_stmt = base_stmt.where(func.date(Measurement.date_time) >= date_filters.from_date)
        if date_filters.to_date:
            base_stmt = base_stmt.where(func.date(Measurement.date_time) <= date_filters.to_date)
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Measurement, paging)
        items = self.db_session.execute(items_stmt).scalars().all()

        result = PagedResultResponse(total_count = total_count, items = items)

        return result

    def get_latest_measurement_by_port_id(self, port_id: int):
        stmt = (
            select(Measurement)
            .where(Measurement.port_id == port_id)
            .order_by(desc(Measurement.date_time))
            .limit(1)
        )
        result = self.db_session.execute(stmt)
        return result.scalars().first()
