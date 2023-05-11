"""Basic tests with mocked device"""
from app.core.device import StatusResponse


def test_send_status(mocked_device):
    response = mocked_device.read_status()
    assert type(response) is StatusResponse
    assert response.is_success
    assert response.controls
    assert response.sensors


def test_read_sensor(mocked_device):
    pass


def test_send_action(mocked_device):
    status = mocked_device.read_status()
    for control in status.sensors.keys():
        response = mocked_device.send_control(control)
        assert response.is_success
