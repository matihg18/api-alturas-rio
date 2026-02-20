from fastapi import FastAPI, Depends
from api.schemas import (
    MeasurementResponse,
    PortResponse,
    PagingParams,
    DateFilters,
    PagedResultResponse
)
from typing import List, Optional
from api.repository import ApiRepository
from common.database import SessionLocal
from sqlalchemy.orm import Session
from datetime import date

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ports", response_model=List[PortResponse])
def get_ports(db: Session = Depends(get_db)):
    repository = ApiRepository(db)
    return repository.get_port_list()


@app.get("/ports/{port_id}", response_model=PortResponse)
def get_port_by_port_id(
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_port_by_port_id(port_id)


@app.get("/measurements/{port_id}", response_model=PagedResultResponse[MeasurementResponse])
def get_measurements_by_port_id(
    port_id: int,
    paging: PagingParams = Depends(),
    date_filters: DateFilters = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_measurements_by_port_id(port_id, paging, date_filters)


@app.get("/measurements/latest/{port_id}", response_model=MeasurementResponse)
def get_latest_measurement_by_port_id(
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_latest_measurement_by_port_id(port_id)


@app.get("/alerts", response_model=PagedResultResponse[PortResponse])
def get_ports_with_heigth_alert(
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_height_alert(paging)


@app.get("/alerts/evacuation", response_model=PagedResultResponse[PortResponse])
def get_ports_with_evacutation_alert(
    paging: PagingParams = Depends(),
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_ports_with_evacutation_alert(paging)
