import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.database import Base


@pytest.fixture
def db_session():
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


@pytest.fixture
def html_pagina_principal():
    return """
    <html><body>
    <table>
        <tbody>
            <tr class="">
                <th data-label="Puerto:">COLON</th>
                <td data-label="Río:">URUGUAY</td>
                <td data-label="Ultimo Registro:" class="warning">2.15</td>
                <td data-label="Variacion">0.40</td>
                <td data-label="Periodo">12</td>
                <td data-label="Fecha Hora:"><b>14/FEB/26 - 1200</b></td>
                <td data-label="Estado:">CRECE</td>
                <td><img src="img/arriba.svg" width="40" /></td>
                <td data-label="Registro Anterior:">1.75</td>
                <td data-label="Fecha Anterior:">13/FEB/26 - 1200</td>
                <td data-label="Alerta:">7.10</td>
                <td data-label="Evacuación:">7.90</td>
                <td><a href="/alturas/?page=historico&amp;tiempo=7&amp;id=550"
                    target="_blank"><i class="fa fa-2x fa-line-chart"></i></a></td>
            </tr>
            <tr class="">
                <th data-label="Puerto:">CONCORDIA</th>
                <td data-label="Río:">URUGUAY</td>
                <td data-label="Ultimo Registro:">3.50</td>
                <td data-label="Variacion">-0.10</td>
                <td data-label="Periodo">12</td>
                <td data-label="Fecha Hora:"><b>14/FEB/26 - 1200</b></td>
                <td data-label="Estado:">BAJA</td>
                <td><img src="img/abajo.svg" width="40" /></td>
                <td data-label="Registro Anterior:">3.60</td>
                <td data-label="Fecha Anterior:">13/FEB/26 - 1200</td>
                <td data-label="Alerta:">10.50</td>
                <td data-label="Evacuación:">13.50</td>
                <td><a href="/alturas/?page=historico&amp;tiempo=7&amp;id=500"
                    target="_blank"><i class="fa fa-2x fa-line-chart"></i></a></td>
            </tr>
        </tbody>
    </table>
    </body></html>
    """


@pytest.fixture
def html_historico_normal():
    return """
    <html><body>
    <script>
        Highcharts.chart('container', {
            series: [{
                type: 'area',
                name: 'Registro',
                data: [[1707904800000,2.15],[1707861600000,1.75],[1707818400000,1.50]]
            },{
                name: 'Alerta',
                data: [[1707904800000,7.10]]
            }]
        });
    </script>
    </body></html>
    """


@pytest.fixture
def html_historico_con_array():
    return """
    <html><body>
    <script>
        Highcharts.chart('container', {
            series: [{
                type: 'area',
                name: 'Registro',
                data: [[1707904800000,2.15],[1707861600000,Array],[1707818400000,1.50],[1707775200000,Array]]
            }]
        });
    </script>
    </body></html>
    """


@pytest.fixture
def html_historico_sin_datos():
    return """
    <html><body>
    <span>No hay registros para mostrar</span>
    </body></html>
    """
