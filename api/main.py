from fastapi import FastAPI, Depends, HTTPException, Request
from api.schemas import (
    MeasurementResponse,
    PortResponse,
    PagingParams,
    DateFilters,
    PagedResultResponse
)
from api.repository import ApiRepository
from api.rate_limiter import limiter, rate_limit_exceeded_handler, RATE_LIMIT_DEFAULT
from common.database import SessionLocal
from sqlalchemy.orm import Session
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ports", response_model=PagedResultResponse[PortResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_ports(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_port_list(paging)


@app.get("/ports/{port_id}", response_model=PortResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_port_by_port_id(
    request: Request,
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    port = repository.get_port_by_port_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with id:{port_id} not found")
    return port


@app.get("/measurements/{port_id}", response_model=PagedResultResponse[MeasurementResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_measurements_by_port_id(
    request: Request,
    port_id: int,
    paging: PagingParams = Depends(),
    date_filters: DateFilters = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    port = repository.get_port_by_port_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with id {port_id} not found")
    return repository.get_measurements_by_port_id(port_id, paging, date_filters)


@app.get("/measurements/latest/{port_id}", response_model=MeasurementResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_latest_measurement_by_port_id(
    request: Request,
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)

    port = repository.get_port_by_port_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with id {port_id} not found")

    measurement = repository.get_latest_measurement_by_port_id(port_id)
    if not measurement:
        raise HTTPException(status_code=404, detail=f"No measurements found for port {port_id}")

    return repository.get_latest_measurement_by_port_id(port_id)


@app.get("/alerts", response_model=PagedResultResponse[PortResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_ports_with_active_alert(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_active_alert(paging)


@app.get("/alerts/evacuation", response_model=PagedResultResponse[PortResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_ports_with_evacuation_alert(
    request: Request,
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_evacuation_alert(paging)
