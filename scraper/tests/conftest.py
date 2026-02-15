import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.database import Base


@pytest.fixture
def db_session():
    # Creamos una DB en memoria para el test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def html_ejemplo_prefectura():
    return """
    <html>
        <body>
            <script>
                var mapData = '[{
                "PUERTO":"COLON",
                "RIO":"URUGUAY",
                "LATITUD":"-32.22",
                "LONGITUD":"-58.14",
                "ULTIMOREGISTRO":"2.15",
                "ALERTA":"7.10",
                "EVACUACION":"7.90",
                "ESTADO":"CRECE",
                "VARIACION":"0.40",
                "FECHAHORA":"14/FEB/26 - 1200"}
                ,{"PUERTO":"IGUAZU",
                "RIO":"IGUAZU",
                "LATITUD":"-25.59",
                "LONGITUD":"-54.58",
                "ULTIMOREGISTRO":"8.80",
                "ALERTA":"25.00",
                "EVACUACION":"28.00",
                "ESTADO":"BAJA",
                "VARIACION":"-0.70",
                "FECHAHORA":"14/FEB/26 - 1200"}]';
            </script>
        </body>
    </html>
    """


@pytest.fixture
def html_datos_invalidos():
    return """
    <html>
        <script>
            var mapData = '[{
                "PUERTO":"TEST_ERROR",
                "RIO":"URUGUAY",
                "LATITUD":"0",
                "LONGITUD":"0",
                "ULTIMOREGISTRO":"-",
                "ALERTA":"S/E",
                "EVACUACION":"",
                "ESTADO":"ST",
                "VARIACION":"-",
                "FECHAHORA":"14/FEB/26 - 1200"
            }]';
        </script>
    </html>
    """
