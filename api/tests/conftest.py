import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app, get_db
from common.database import Base
from common.models import Port, Measurement
from datetime import date
from fastapi.testclient import TestClient
import os

DB_USER = os.getenv("DB_TEST_USER", "postgres")
DB_PASS = os.getenv("DB_TEST_PASSWORD", "password")
DB_NAME = os.getenv("DB_TEST_NAME", "rio_db")
DB_HOST = os.getenv("DB_HOST", "db")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
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
    port_1 = Port(
        id=1,
        name="testPort1",
        river="testRiver",
        alert_value=5.0,
        evacuation_value=7.0,
        latitud=30.00,
        longitud=50.00
    )
    port_2 = Port(
        id=2,
        name="testPort2",
        river="testRiver",
        alert_value=3.0,
        evacuation_value=4.0,
        latitud=50.00,
        longitud=30.00
    )
    port_3 = Port(
        id=3,
        name="testPort3",
        river="testRiver",
        alert_value=5.0,
        evacuation_value=7.0,
        latitud=50.00,
        longitud=30.00
    )
    measurement_1 = Measurement(
        id=1,
        port_id=1,
        date_time=date(2026, 2, 21),
        value=4.7,
        state="CRECE",
        delta=0.3,
    )
    measurement_2 = Measurement(
        id=2,
        port_id=1,
        date_time=date(2026, 2, 22),
        value=5.1,
        state="CRECE",
        delta=0.4,
    )
    measurement_3 = Measurement(
        id=3,
        port_id=2,
        date_time=date(2026, 2, 22),
        value=4.1,
        state="BAJA",
        delta=0.4,
    )
    db_session.add_all([port_1, port_2, port_3, measurement_1, measurement_2, measurement_3])
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
