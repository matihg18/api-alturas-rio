from fastapi import FastAPI, Depends, HTTPException, Request
from api.schemas import (
    MeasurementResponse,
    StationResponse,
    PagingParams,
    DateFilters,
    PagedResultResponse
)
from api.repository import ApiRepository
from api.rate_limiter import limiter, rate_limit_exceeded_handler, RATE_LIMIT_DEFAULT
from common.database import SessionLocal
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from common.database import engine
from common.models import Base
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@app.get("/measurements/{station_id}", response_model=PagedResultResponse[MeasurementResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_measurements_by_station_id(
    request: Request,
    station_id: int,
    paging: PagingParams = Depends(),
    date_filters: DateFilters = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    station = repository.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with id {station_id} not found")
    return repository.get_measurements_by_station_id(station_id, paging, date_filters)


@app.get("/measurements/latest/{station_id}", response_model=MeasurementResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_latest_measurement_by_station_id(
    request: Request,
    station_id: int,
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

    return measurement


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
