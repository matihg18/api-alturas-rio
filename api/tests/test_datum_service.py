from common.datum_service import convert, get_offset


# --- Tests de convert() ---

def test_convert_adds_offset():
    assert convert(4.7, 1.0) == 5.7


def test_convert_negative_offset():
    assert convert(4.7, -0.52) == 4.18


def test_convert_rounds_to_2_decimals():
    # 5.1 + 1.0 = 6.1 exacto, sin ruido
    assert convert(5.1, 1.0) == 6.1
    # Operación que normalmente genera ruido de punto flotante
    result = convert(1.4, -0.05)
    assert result == 1.35
    assert isinstance(result, float)


# --- Tests de get_offset() ---

def test_get_offset_station_with_gauge_point(db_session, seed_data):
    # station_1 tiene gauge_point con offset IGN = 1.0
    offset = get_offset(db_session, station_id=1, datum_code="IGN")
    assert offset == 1.0


def test_get_offset_station_without_gauge_point(db_session, seed_data):
    # station_2 no tiene gauge_point → None
    offset = get_offset(db_session, station_id=2, datum_code="IGN")
    assert offset is None


def test_get_offset_datum_not_found(db_session, seed_data):
    # station_1 tiene gauge_point pero no tiene datum WHARTON
    offset = get_offset(db_session, station_id=1, datum_code="WHARTON")
    assert offset is None


def test_get_offset_station_not_found(db_session, seed_data):
    # station inexistente → None
    offset = get_offset(db_session, station_id=999, datum_code="IGN")
    assert offset is None


def test_get_offset_case_insensitive(db_session, seed_data):
    # El código del datum se normaliza a mayúsculas internamente
    offset = get_offset(db_session, station_id=1, datum_code="ign")
    assert offset == 1.0
