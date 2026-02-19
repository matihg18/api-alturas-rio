from pydantic import BaseModel, ConfigDict
from typing import Optional, Generic, TypeVar, List
from datetime import datetime
from fastapi import Query


T = TypeVar("T")


class PagedAndSortedRequest:
    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        sorting: Optional[str] = Query(None)
    ):
        self.skip = skip
        self.limit = limit
        self.sorting = sorting


class PagedResultResponse(BaseModel, Generic[T]):
    total_count: int
    items: List[T]


class PortBase (BaseModel):
    name: str
    river: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    alert_value: Optional[float] = None
    evacuation_value: Optional[float] = None


class PortResponse (PortBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class MeasurementBase (BaseModel):
    port_id: int
    date_time: datetime
    value: float
    state: Optional[str] = None
    delta: Optional[float] = 0.0


class MeasurementResponse (MeasurementBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
