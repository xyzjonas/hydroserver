import pytest
from app.core.device import StatusResponse, Status


@pytest.mark.parametrize('data', [
    {'status': 'ok'},
    {}
])
def test_status_response(data):
    response = StatusResponse.from_response_data(data)
    assert response.status


@pytest.mark.parametrize('data', [
    {}
])
def test_status_response_no_data(data):
    response = StatusResponse.from_response_data(data)
    assert not response.is_success
    assert response.status is Status.NO_DATA
