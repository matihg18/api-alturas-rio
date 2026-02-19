from fastapi import FastAPI, Depends
from api.schemas import MeasurementResponse, PortResponse
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


@app.get("/measurements/{port_id}", response_model=List[MeasurementResponse])
def get_measurements_by_port_id(
    port_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_measurements_by_port_id(port_id, from_date, to_date)


@app.get("/measurements/latest/{port_id}", response_model=MeasurementResponse)
def get_latest_measurement_by_port_id(
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_latest_measurement_by_port_id(port_id)


@app.get("/alerts", response_model=List[PortResponse])
def get_ports_with_heigth_alert(db: Session = Depends(get_db)):
    repository = ApiRepository(db)
    return repository.get_ports_with_height_alert()


@app.get("/alerts/evacuation", response_model=List[PortResponse])
def get_ports_with_evacutation_alert(db: Session = Depends(get_db)):
    repository = ApiRepository(db)
    return repository.get_ports_with_evacutation_alert()
