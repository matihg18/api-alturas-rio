from fastapi import FastAPI, Depends, HTTPException
from api.schemas import (
    MeasurementResponse,
    PortResponse,
    PagingParams,
    DateFilters,
    PagedResultResponse
)
from api.repository import ApiRepository
from common.database import SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ports", response_model=PagedResultResponse[PortResponse])
def get_ports(
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_port_list(paging)


@app.get("/ports/{port_id}", response_model=PortResponse)
def get_port_by_port_id(
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    port = repository.get_port_by_port_id(port_id)
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with id:{port_id} not found")
    return port


@app.get("/measurements/{port_id}", response_model=PagedResultResponse[MeasurementResponse])
def get_measurements_by_port_id(
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
def get_latest_measurement_by_port_id(
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
def get_ports_with_active_alert(
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_active_alert(paging)


@app.get("/alerts/evacuation", response_model=PagedResultResponse[PortResponse])
def get_ports_with_evacuation_alert(
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_evacuation_alert(paging)
