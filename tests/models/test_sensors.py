import math

import pytest
import random
import timeit
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
@pytest.mark.parametrize("wanted_count", [20, 1000])
def test_get_last_values_count(mocked_device_with_sensor_and_control, count, wanted_count):
    _, sensor, _ = mocked_device_with_sensor_and_control
    for _ in range(count):
        val = random.randint(0, 100)
        db.session.add(HistoryItem(sensor=sensor, _value=val, timestamp=datetime.utcnow()))
    db.session.commit()

    if wanted_count > count:
        wanted_count = count

    filtered = sensor.get_last_values(count=wanted_count)
    assert len(filtered) == wanted_count


@pytest.mark.skip(reason="manual")
@pytest.mark.parametrize("count", [10000])
def test_sensor_query_performance(mocked_device_with_sensor_and_control, count):
    _, sensor, _ = mocked_device_with_sensor_and_control

    old_time = datetime(2020, 9, 23, 12, 20)
    for _ in range(count):
        val = random.randint(0, 100)
        db.session.add(HistoryItem(sensor=sensor, _value=val, timestamp=old_time))
    for _ in range(count):
        val = random.randint(0, 100)
        db.session.add(HistoryItem(sensor=sensor, _value=val, timestamp=datetime.utcnow()))
    db.session.commit()

    def x_test_code():
        return sensor.get_last_values(count=10)

    def y_test_code():
        return sensor.get_last_values(count=10, since=datetime(2021, 1, 1))

    repeat = 1
    x = timeit.timeit(stmt=x_test_code, number=repeat)
    print("\nTIME X: {}".format(x/repeat))

    y = timeit.timeit(stmt=y_test_code, number=repeat)
    print("\nTIME Y: {}".format(y / repeat))

