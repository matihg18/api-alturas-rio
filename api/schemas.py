from pydantic import BaseModel, ConfigDict
from typing import Optional, Generic, TypeVar, List
from datetime import datetime, date
from fastapi import Query


T = TypeVar("T")


class PagingParams:
    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        sorting: Optional[str] = Query(None)
    ):
        self.skip = skip
        self.limit = limit
        self.sorting = sorting


class DateFilters:
    def __init__(
        self,
        from_date: Optional[date] = Query(None),
        to_date: Optional[date] = Query(None)
    ):
        self.from_date = from_date
        self.to_date = to_date


class PagedResultResponse(BaseModel, Generic[T]):
    total_count: int
    items: List[T]


class StationBase(BaseModel):
    name: str
    river: str
    source: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    alert_value: Optional[float] = None
    evacuation_value: Optional[float] = None


class StationResponse(StationBase):
    id: int
    is_visible: bool = True
    gauge_point_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class MeasurementBase(BaseModel):
    station_id: int
    date_time: datetime
    value: float


class MeasurementResponse(MeasurementBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PagedMeasurementResponse(BaseModel):
    total_count: int
    datum_used: str = "LOCAL"
    conversion_available: bool = False
    items: List[MeasurementResponse]


class LatestMeasurementResponse(MeasurementResponse):
    datum_used: str = "LOCAL"
    conversion_available: bool = False


class ReferenceZeroTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class GaugeDatumResponse(BaseModel):
    id: int
    offset_local_to_datum: float
    datum_type: ReferenceZeroTypeResponse
    model_config = ConfigDict(from_attributes=True)


class GaugePointResponse(BaseModel):
    id: int
    name: str
    river: Optional[str] = None
    description: Optional[str] = None
    datums: List[GaugeDatumResponse] = []
    model_config = ConfigDict(from_attributes=True)
