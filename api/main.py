from fastapi import FastAPI, Depends
from api.schemas import MeasurementResponse, PortResponse
from typing import List
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


@app.get("/ports/", response_model=List[PortResponse])
def get_ports(db: Session = Depends(get_db)):
    repository = ApiRepository(db)
    return repository.get_port_list()


@app.get("/measurements/{port_id}", response_model=List[MeasurementResponse])
def get_measurements_by_port_id(
    port_id: int,
    db: Session = Depends(get_db)
):
    repository = ApiRepository(db)
    return repository.get_measurements_by_port_id(port_id)
