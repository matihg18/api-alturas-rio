from api.repository import ApiRepository
from api.schemas import PagingParams, DateFilters


def test_get_stations_list(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=2, sorting=None)
    result = repository.get_station_list(params)

    assert result.total_count == 3
    assert result.items[1].id == 2


def test_sorting_applying(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=1, limit=2, sorting="alert_value-desc")
    result = repository.get_station_list(params)

    assert result.total_count == 3
    assert result.items[0].id == 3
    assert result.items[1].id == 2


def test_get_station_by_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_station_by_id(1)
    assert result.name == "testStation1"
    assert result.gauge_point_id == 1


def test_get_station_with_active_alert(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    result = repository.get_stations_with_active_alert(params)
    assert result.total_count == 2
    assert result.items[0].id == 1


def test_get_station_with_evacuation_alert(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    result = repository.get_stations_with_evacuation_alert(params)
    assert result.total_count == 1
    assert result.items[0].id == 2


def test_get_measurement_by_station_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    date_filters = DateFilters(from_date=None, to_date=None)
    result = repository.get_measurements_by_station_id(
        station_id=1,
        paging=params,
        date_filters=date_filters
    )
    assert result.total_count == 2


def test_get_latest_measurement_by_station_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_latest_measurement_by_station_id(1)
    assert result.value == 5.1


def test_get_datum_types(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_datum_types()
    assert len(result) == 1
    assert result[0].code == "IGN"


def test_get_gauge_point_for_station_linked(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_gauge_point_for_station(1)
    assert result is not None
    assert result.name == "TestPoint"
    assert len(result.datums) == 1
    assert result.datums[0].offset_local_to_datum == 1.0


def test_get_gauge_point_for_station_not_linked(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_gauge_point_for_station(2)
    assert result is None
