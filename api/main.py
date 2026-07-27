from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from api.schemas import (
    MeasurementResponse,
    PagedMeasurementResponse,
    LatestMeasurementResponse,
    StationResponse,
    PagingParams,
    DateFilters,
    PagedResultResponse,
    ReferenceZeroTypeResponse,
    GaugePointResponse,
)
from api.repository import ApiRepository
from api.rate_limiter import limiter, rate_limit_exceeded_handler, RATE_LIMIT_DEFAULT
from api.dependencies import get_db
from common.datum_service import get_offset, convert as datum_convert
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from common.database import engine
from common.models import Base
from api.admin_router import router as admin_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(admin_router, prefix="/admin", tags=["admin"])




def _get_datum_context(db: Session, station_id: int, datum: Optional[str]):
    if not datum:
        return None, "LOCAL", False
    offset = get_offset(db, station_id, datum.upper())
    if offset is not None:
        return offset, datum.upper(), True
    return None, "LOCAL", False


@app.get("/stations", response_model=PagedResultResponse[StationResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_stations(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_station_list(paging)


@app.get("/stations/{station_id}", response_model=StationResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_station_by_id(
    request: Request,
    station_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    station = repository.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with id:{station_id} not found")
    return station


@app.get("/measurements/{station_id}", response_model=PagedMeasurementResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_measurements_by_station_id(
    request: Request,
    station_id: int,
    paging: PagingParams = Depends(),
    date_filters: DateFilters = Depends(),
    datum: Optional[str] = Query(None, description="Código de datum destino: IGN, WHARTON"),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    station = repository.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with id {station_id} not found")

    offset, datum_used, conversion_available = _get_datum_context(db, station_id, datum)
    result = repository.get_measurements_by_station_id(station_id, paging, date_filters)

    items = []
    for m in result.items:
        item = MeasurementResponse.model_validate(m)
        if offset is not None:
            item.value = datum_convert(m.value, offset)
        items.append(item)

    return PagedMeasurementResponse(
        total_count=result.total_count,
        datum_used=datum_used,
        conversion_available=conversion_available,
        items=items,
    )


@app.get("/measurements/latest/{station_id}", response_model=LatestMeasurementResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_latest_measurement_by_station_id(
    request: Request,
    station_id: int,
    datum: Optional[str] = Query(None, description="Código de datum destino: IGN, WHARTON"),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)

    station = repository.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with id {station_id} not found")

    measurement = repository.get_latest_measurement_by_station_id(station_id)
    if not measurement:
        raise HTTPException(
            status_code=404,
            detail=f"No measurements found for station {station_id}"
        )

    offset, datum_used, conversion_available = _get_datum_context(db, station_id, datum)
    response = LatestMeasurementResponse.model_validate(measurement)
    response.datum_used = datum_used
    response.conversion_available = conversion_available
    if offset is not None:
        response.value = datum_convert(measurement.value, offset)
    return response


@app.get("/alerts", response_model=PagedResultResponse[StationResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_stations_with_active_alert(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_stations_with_active_alert(paging)


@app.get("/alerts/evacuation", response_model=PagedResultResponse[StationResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_stations_with_evacuation_alert(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_stations_with_evacuation_alert(paging)


@app.get("/datums", response_model=List[ReferenceZeroTypeResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_datum_types(
    request: Request,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_datum_types()


@app.get("/datums/station/{station_id}", response_model=GaugePointResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_gauge_point_for_station(
    request: Request,
    station_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    station = repository.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with id {station_id} not found")

    gauge_point = repository.get_gauge_point_for_station(station_id)
    if not gauge_point:
        raise HTTPException(
            status_code=404,
            detail=f"Station {station_id} has no gauge point assigned"
        )

    return gauge_point
