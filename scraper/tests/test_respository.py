from repository import ScraperRepository
from parser import RawPortData
from common.models import Port, Measurement


def test_save_all_filters_by_river(db_session, monkeypatch):
    monkeypatch.setenv("ALLOWED_RIVERS", "URUGUAY")
    repo = ScraperRepository(db_session)

    datos = [
        RawPortData(PUERTO="COLON", RIO="URUGUAY", LATITUD=-32.22, LONGITUD=-58.13,
                    ESTADO="ST", VARIACION="0", FECHAHORA="14/FEB/26 - 1200"),
        RawPortData(PUERTO="ROSARIO", RIO="PARANA", LATITUD=-32.94, LONGITUD=-60.63,
                    ESTADO="ST", VARIACION="0", FECHAHORA="14/FEB/26 - 1200")
    ]

    repo.save_all(datos)

    puertos = db_session.query(Port).all()
    assert len(puertos) == 1
    assert puertos[0].name == "COLON"
    assert puertos[0].river == "URUGUAY"


def test_no_duplicate_measurements(db_session, monkeypatch):
    monkeypatch.setenv("ALLOWED_RIVERS", "URUGUAY")
    repo = ScraperRepository(db_session)

    dato_unico = [
        RawPortData(PUERTO="COLON", RIO="URUGUAY", LATITUD=-32.22, LONGITUD=-58.13,
                    ULTIMOREGISTRO="2.15", ESTADO="ST", VARIACION="0", FECHAHORA="14/FEB/26 - 1200")
    ]

    repo.save_all(dato_unico)
    repo.save_all(dato_unico)

    puerto = db_session.query(Port).filter_by(name="COLON").first()
    mediciones = db_session.query(Measurement).filter_by(port_id=puerto.id).all()

    assert len(mediciones) == 1
    assert mediciones[0].value == 2.15
