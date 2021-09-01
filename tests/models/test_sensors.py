import pytest
import random
from datetime import datetime

from app import db
from app.models import HistoryItem


@pytest.mark.parametrize("data_since_expected", [
    (
            {
                datetime(2020, 8, 30, 12, 30): "12",
                datetime(2020, 8, 30, 13, 30): "12",
                datetime(2020, 8, 30, 14, 30): "12",
            }, datetime(2020, 8, 30, 12, 40), 2
    ),
    (
            {
                datetime(2020, 8, 30, 12, 30): "12",
                datetime(2020, 8, 30, 13, 30): "12",
                datetime(2020, 8, 30, 14, 30): "12",
            }, datetime(2020, 8, 31, 12, 40), 0
    ),
    (
            {
                datetime(2020, 8, 30, 12, 30): "12",
                datetime(2020, 8, 30, 13, 30): "12",
                datetime(2020, 8, 30, 14, 30): "12",
            }, datetime(2020, 8, 29, 12, 40), 3
    ),
], ids=["2/3", "after_zero", "before_all"])
def test_get_last_values_since(mocked_device_with_sensor_and_control, data_since_expected):
    _, sensor, _ = mocked_device_with_sensor_and_control
    data, since, expected = data_since_expected
    for date, val in data.items():
        db.session.add(HistoryItem(sensor=sensor, _value=val, timestamp=date))
    db.session.commit()

    filtered = sensor.get_last_values(since=since)
    assert len(filtered) == expected


@pytest.mark.parametrize("count", [0, 11, 13, 99, 100, 111, 999])
@pytest.mark.parametrize("wated_count", [20, 1000])
def test_get_last_values_count(mocked_device_with_sensor_and_control, count, wated_count):
    _, sensor, _ = mocked_device_with_sensor_and_control
    for _ in range(count):
        val = random.randint(0, 100)
        db.session.add(HistoryItem(sensor=sensor, _value=val, timestamp=datetime.utcnow()))
    db.session.commit()
    filtered = sensor.get_last_values(num=wated_count)
    assert len(filtered) == wated_count

