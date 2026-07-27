from pydantic import BaseModel, ConfigDict
from typing import Optional


# ── Gauge Points ─────────────────────────────────────────────────────────────

class GaugePointCreate(BaseModel):
    name: str
    river: Optional[str] = None
    description: Optional[str] = None


class GaugePointUpdate(BaseModel):
    name: Optional[str] = None
    river: Optional[str] = None
    description: Optional[str] = None


# ── Datum Types (ReferenceZeroType) ─────────────────────────────────────────

class DatumTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class DatumTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ── Offsets (GaugeDatum) ─────────────────────────────────────────────────────

class OffsetCreate(BaseModel):
    gauge_point_id: int
    datum_type_id: int
    offset_local_to_datum: float


class OffsetUpdate(BaseModel):
    offset_local_to_datum: float


# ── Stations ─────────────────────────────────────────────────────────────────

class StationAssignGaugePoint(BaseModel):
    gauge_point_id: Optional[int] = None


# ── Response models ──────────────────────────────────────────────────────────

class DatumTypeAdminResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class GaugePointAdminResponse(BaseModel):
    id: int
    name: str
    river: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class OffsetAdminResponse(BaseModel):
    id: int
    gauge_point_id: int
    datum_type_id: int
    offset_local_to_datum: float
    gauge_point: GaugePointAdminResponse
    datum_type: DatumTypeAdminResponse
    model_config = ConfigDict(from_attributes=True)


class StationAdminResponse(BaseModel):
    id: int
    name: str
    river: str
    source: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    alert_value: Optional[float] = None
    evacuation_value: Optional[float] = None
    gauge_point_id: Optional[int] = None
    gauge_point: Optional[GaugePointAdminResponse] = None
    model_config = ConfigDict(from_attributes=True)
