import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.dependencies import get_db
from common.database import Base

from common.models import (
    Station, Measurement,
    GaugePoint, GaugeDatum, ReferenceZeroType
)
from datetime import date
from fastapi.testclient import TestClient
import os

DB_USER = os.getenv("DB_TEST_USER", "postgres")
DB_PASS = os.getenv("DB_TEST_PASSWORD", "password")
DB_NAME = os.getenv("DB_TEST_NAME", "rio_db_test")
DB_HOST = os.getenv("DB_HOST", "db")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seed_data(db_session):
    # --- Datum infrastructure ---
    ign_type = ReferenceZeroType(
        id=1, code="IGN", name="Cero IGN",
        description="Instituto Geográfico Nacional"
    )
    gauge_point = GaugePoint(id=1, name="TestPoint", river="testRiver")
    # offset de +1.0: altura_IGN = altura_local + 1.0
    gauge_datum = GaugeDatum(
        id=1,
        gauge_point_id=1,
        datum_type_id=1,
        offset_local_to_datum=1.0,
    )

    # --- Stations ---
    # station_1: tiene gauge_point → conversión disponible
    station_1 = Station(
        id=1,
        name="testStation1",
        river="testRiver",
        source="prefectura",
        alert_value=5.0,
        evacuation_value=7.0,
        latitud=30.00,
        longitud=50.00,
        gauge_point_id=1,
    )
    # station_2: sin gauge_point → sin conversión
    station_2 = Station(
        id=2,
        name="testStation2",
        river="testRiver",
        source="prefectura",
        alert_value=3.0,
        evacuation_value=4.0,
        latitud=50.00,
        longitud=30.00,
        gauge_point_id=None,
    )
    # station_3: sin gauge_point, sin mediciones
    station_3 = Station(
        id=3,
        name="testStation3",
        river="testRiver",
        source="prefectura",
        alert_value=5.0,
        evacuation_value=7.0,
        latitud=50.00,
        longitud=30.00,
        gauge_point_id=None,
    )

    # --- Measurements ---
    measurement_1 = Measurement(
        id=1, station_id=1,
        date_time=date(2026, 2, 21), value=4.7,
    )
    measurement_2 = Measurement(
        id=2, station_id=1,
        date_time=date(2026, 2, 22), value=5.1,
    )
    measurement_3 = Measurement(
        id=3, station_id=2,
        date_time=date(2026, 2, 22), value=4.1,
    )

    db_session.add_all([
        ign_type, gauge_point, gauge_datum,
        station_1, station_2, station_3,
        measurement_1, measurement_2, measurement_3,
    ])
    db_session.commit()

    # Reset postgres sequences so auto-increment works after manual ID assignment
    from sqlalchemy import text
    tables = ["reference_zero_types", "gauge_points", "gauge_datums", "stations", "measurements"]
    for table in tables:
        db_session.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1)) FROM {table};"
        ))
    db_session.commit()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
