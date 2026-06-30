import requests
from scraper.errors import classify_error


def test_classify_timeout():
    e = requests.exceptions.Timeout()
    error_type, status = classify_error(e)
    assert error_type == "TIMEOUT"
    assert status is None


def test_classify_http_error_with_status():
    response = requests.models.Response()
    response.status_code = 503
    e = requests.exceptions.HTTPError(response=response)
    error_type, status = classify_error(e)
    assert error_type == "HTTP_ERROR"
    assert status == 503


def test_classify_http_error_without_response():
    e = requests.exceptions.HTTPError()
    error_type, status = classify_error(e)
    assert error_type == "HTTP_ERROR"
    assert status is None


def test_classify_connection_error():
    e = requests.exceptions.ConnectionError("No route to host")
    error_type, status = classify_error(e)
    assert error_type == "HTTP_ERROR"
    assert status is None


def test_classify_json_parse_error():
    e = ValueError("No JSON object could be decoded")
    error_type, status = classify_error(e)
    assert error_type == "PARSE_ERROR"
    assert status is None


def test_classify_key_error():
    e = KeyError("nombre")
    error_type, status = classify_error(e)
    assert error_type == "PARSE_ERROR"
    assert status is None


def test_classify_attribute_error():
    e = AttributeError("'NoneType' object has no attribute 'find'")
    error_type, status = classify_error(e)
    assert error_type == "PARSE_ERROR"
    assert status is None


def test_classify_unknown_error():
    e = RuntimeError("Algo inesperado")
    error_type, status = classify_error(e)
    assert error_type == "UNKNOWN"
    assert status is None
