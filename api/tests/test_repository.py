from repository import ApiRepository
from api.schemas import PagingParams, DateFilters


def test_get_ports_list(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=2, sorting=None)
    result = repository.get_port_list(params)

    assert result.total_count == 3
    assert result.items[1].id == 2


def test_sorting_applying(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=1, limit=2, sorting="alert_value-desc")
    result = repository.get_port_list(params)

    assert result.total_count == 3
    assert result.items[0].id == 3
    assert result.items[1].id == 2


def test_get_port_by_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_port_by_port_id(1)
    assert result.name == "testPort1"


def test_get_port_with_active_alert(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    result = repository.get_ports_with_active_alert(params)
    assert result.total_count == 2
    assert result.items[0].id == 1


def test_get_port_with_evacuation_alert(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    result = repository.get_ports_with_evacuation_alert(params)
    assert result.total_count == 1
    assert result.items[0].id == 2


def test_get_measurement_by_port_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    params = PagingParams(skip=0, limit=10, sorting=None)
    date_filters = DateFilters(from_date=None, to_date=None)
    result = repository.get_measurements_by_port_id(
        port_id=1,
        paging=params,
        date_filters=date_filters
    )
    assert result.total_count == 2


def test_get_latest_measurement_by_port_id(db_session, seed_data):
    repository = ApiRepository(db_session)
    result = repository.get_latest_measurement_by_port_id(1)
    assert result.value == 5.1
