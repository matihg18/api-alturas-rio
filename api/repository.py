from sqlalchemy import select, desc, asc, func
from sqlalchemy.orm import Session
from common.models import Measurement, Station, ReferenceZeroType, GaugePoint
from api.schemas import PagedResultResponse, PagingParams, DateFilters


class ApiRepository:
    def __init__(self, session: Session):
        self.db_session = session

    def _apply_paging_and_sorting(self, stmt, model, paging: PagingParams):
        if paging.sorting:
            parts = paging.sorting.split("-")
            col_name = parts[0]
            direction = parts[1].lower() if len(parts) > 1 else "asc"

            if not hasattr(model, col_name):
                raise ValueError(f"Invalid sorting column: {col_name}")

            col_attr = getattr(model, col_name)

            if direction == "desc":
                stmt = stmt.order_by(desc(col_attr))
            else:
                stmt = stmt.order_by(asc(col_attr))

        return stmt.offset(paging.skip).limit(paging.limit)

    def get_station_list(self, paging: PagingParams):
        base_stmt = select(Station)
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Station, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        return PagedResultResponse(total_count=total_count, items=items)

    def get_station_by_id(self, station_id: int):
        stmt = select(Station).where(Station.id == station_id)
        return self.db_session.execute(stmt).scalars().first()

    def get_stations_with_active_alert(self, paging: PagingParams):
        latest_measurements = (
            select(Measurement)
            .distinct(Measurement.station_id)
            .order_by(Measurement.station_id, desc(Measurement.date_time))
            .subquery()
        )
        base_stmt = (
            select(Station)
            .join(latest_measurements, Station.id == latest_measurements.c.station_id)
            .where(latest_measurements.c.value >= Station.alert_value)
        )
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Station, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        return PagedResultResponse(total_count=total_count, items=items)

    def get_stations_with_evacuation_alert(self, paging: PagingParams):
        latest_measurements = (
            select(Measurement)
            .distinct(Measurement.station_id)
            .order_by(Measurement.station_id, desc(Measurement.date_time))
            .subquery()
        )
        base_stmt = (
            select(Station)
            .join(latest_measurements, Station.id == latest_measurements.c.station_id)
            .where(latest_measurements.c.value >= Station.evacuation_value)
        )
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Station, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        return PagedResultResponse(total_count=total_count, items=items)

    def get_measurements_by_station_id(
        self,
        station_id: int,
        paging: PagingParams,
        date_filters: DateFilters
    ):
        base_stmt = select(Measurement).where(Measurement.station_id == station_id)
        if date_filters.from_date:
            base_stmt = base_stmt.where(
                func.date(Measurement.date_time) >= date_filters.from_date
            )
        if date_filters.to_date:
            base_stmt = base_stmt.where(
                func.date(Measurement.date_time) <= date_filters.to_date
            )
        total_count = self.db_session.execute(
            select(func.count()).select_from(base_stmt.subquery())
        ).scalar()
        items_stmt = self._apply_paging_and_sorting(base_stmt, Measurement, paging)
        items = self.db_session.execute(items_stmt).scalars().all()
        return PagedResultResponse(total_count=total_count, items=items)

    def get_latest_measurement_by_station_id(self, station_id: int):
        stmt = (
            select(Measurement)
            .where(Measurement.station_id == station_id)
            .order_by(desc(Measurement.date_time))
            .limit(1)
        )
        return self.db_session.execute(stmt).scalars().first()

    def get_datum_types(self):
        stmt = select(ReferenceZeroType)
        return self.db_session.execute(stmt).scalars().all()

    def get_gauge_point_for_station(self, station_id: int):
        station = self.db_session.get(Station, station_id)
        if not station or station.gauge_point_id is None:
            return None
        return self.db_session.get(GaugePoint, station.gauge_point_id)
