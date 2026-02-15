import requests
from scraper.client import PrefecturaClient


def test_fetch_data_success(mocker, html_ejemplo_prefectura):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = html_ejemplo_prefectura
    mocker.patch("requests.get", return_value=mock_response)

    client = PrefecturaClient()

    result = client.fetch_data()

    assert result == html_ejemplo_prefectura
    assert requests.get.called


def test_fetch_data_http_error(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mocker.patch("requests.get", return_value=mock_response)

    client = PrefecturaClient()

    result = client.fetch_data()

    assert result == ""


def test_fetch_data_timeout(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    client = PrefecturaClient()

    result = client.fetch_data()

    assert result == ""
