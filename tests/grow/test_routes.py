import pytest

from app import db
from app.grow.models import GrowSystem, GrowSystemInstance, GrowProperty, GrowPropertyInstance


@pytest.fixture()
def setup_blueprints(mocked_device_with_sensor_and_control):
    m, s, c = mocked_device_with_sensor_and_control

    prop = GrowProperty(name='ph', description='ph of the solution')
    prop_inst = GrowPropertyInstance(grow_property=prop, sensor=s, control=c)

    prop2 = GrowProperty(name='ec', description='ec of the solution')
    prop_inst2 = GrowPropertyInstance(grow_property=prop, sensor=s, control=c)

    prop3 = GrowProperty(name='reservoir', description='tank capacity')

    system = GrowSystem(name='nft', description='just a dummy system')
    system.properties = [prop, prop2, prop3]
    db.session.add(system)
    db.session.commit()

    system_id = system
    return [prop, prop2, prop3], [prop_inst, prop_inst2], system


@pytest.fixture()
def setup(mocked_device_with_sensor_and_control, setup_blueprints):
    m, s, c = mocked_device_with_sensor_and_control
    props, prop_instances, system = setup_blueprints

    my_nft = GrowSystemInstance(grow_system=system, device=m)
    my_nft.grow_properties = prop_instances
    db.session.add(my_nft)
    db.session.commit()


def test_get_system_blueprints(setup, app_setup):
    url = '/grow/systems'
    with app_setup.test_client() as client:
        response = client.get(url)
        assert response.status_code == 200
        assert response.json


def test_get_system_instance(mocked_device_with_sensor_and_control, setup, app_setup):
    device, _, _ = mocked_device_with_sensor_and_control
    url = f'/grow/systems/{device.id}'
    with app_setup.test_client() as client:
        response = client.get(url)
        assert response.status_code == 200
        assert response.json

        data = response.json
        assert data['device']
        assert data['grow_properties']


def test_assign_system_to_device(mocked_device_with_sensor_and_control,
                                 app_setup,
                                 setup_blueprints):
    device, _, _ = mocked_device_with_sensor_and_control
    props, _, system = setup_blueprints
    url = f'/grow/systems/{device.id}'
    with app_setup.test_client() as client:
        response = client.post(url, json={'system_id': system.id})
        assert response.status_code == 201

    system_instance = GrowSystemInstance.query.filter_by(device=device).first()
    assert system_instance
    for prop in system.properties:
        assert prop.name in [g.name for g in system_instance.grow_properties]


@pytest.fixture()
def prepare_for_delete(mocked_device_with_sensor_and_control, setup_blueprints, app_setup):
    device, _, _ = mocked_device_with_sensor_and_control
    props, _, system = setup_blueprints
    url = f'/grow/systems/{device.id}'
    with app_setup.test_client() as client:
        response = client.post(url, json={'system_id': system.id})
        assert response.status_code == 201

    system_instance = GrowSystemInstance.query.filter_by(device=device).first()
    assert system_instance
    for prop in system.properties:
        assert prop.name in [g.name for g in system_instance.grow_properties]

    return system_instance


def test_unassign_system_from_device(mocked_device_and_db, prepare_for_delete, app_setup):
    device = mocked_device_and_db

    assert GrowSystemInstance.query.filter_by(device_id=device.id).first()

    url = f'/grow/systems/{device.id}'
    with app_setup.test_client() as client:
        response = client.delete(url)
        assert response.status_code == 200

    assert not GrowSystemInstance.query.filter_by(device_id=device.id).first()


def test_assign_control(mocked_device_with_sensor_and_control,
                        setup_blueprints, prepare_for_delete, app_setup):
    device, _, _ = mocked_device_with_sensor_and_control
    # props, _, system = setup_blueprints

    system_instance = prepare_for_delete
    prop_instance = system_instance.grow_properties[0]
    sensor = device.sensors[0]

    url = f'/grow/systems/{device.id}/properties/{prop_instance.id}'
    with app_setup.test_client() as client:
        response = client.post(url, json={'sensor_id': sensor.id})
        assert response.status_code == 200

    assert GrowPropertyInstance.query.filter_by(sensor_id=sensor.id).first()