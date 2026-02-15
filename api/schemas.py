from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


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
