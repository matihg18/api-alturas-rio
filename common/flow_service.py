import logging
from datetime import datetime

from sqlalchemy.orm import Session

from common.models import DischargeCurveParams, FlowMeasurement
from common.flow_calculator import compute_flow

logger = logging.getLogger(__name__)


class FlowService:

    def __init__(self, db: Session):
        self.db = db
        self._params_cache: dict[int, DischargeCurveParams | None] = {}

    def get_params(self, station_id: int) -> DischargeCurveParams | None:

        if station_id not in self._params_cache:
            params = (
                self.db.query(DischargeCurveParams)
                .filter_by(station_id=station_id)
                .first()
            )
            self._params_cache[station_id] = params
        return self._params_cache[station_id]

    def compute_and_save(
        self, station_id: int, date_time: datetime, h: float
    ) -> bool:
        params = self.get_params(station_id)
        if params is None:
            return False

        flow = compute_flow(h, params.a, params.b, params.h0)
        if flow is None:
            logger.debug(
                "station_id=%d: H=%.4f ≤ H₀=%.4f — caudal omitido (fuera de rango físico).",
                station_id, h, params.h0,
            )
            return False

        exists = (
            self.db.query(FlowMeasurement)
            .filter_by(station_id=station_id, date_time=date_time)
            .first()
        )
        if exists:
            return False

        self.db.add(FlowMeasurement(
            station_id=station_id,
            date_time=date_time,
            flow=flow,
        ))
        return True
