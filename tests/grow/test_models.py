from app import db
from app.grow.models import GrowProperty, GrowPropertyInstance, GrowSystem, GrowSystemInstance


def test_grow_property(mocked_device_with_sensor_and_control):
    d, s, c = mocked_device_with_sensor_and_control

    prop = GrowProperty(name='ph', description='ph of the solution')
    prop_inst = GrowPropertyInstance(grow_property=prop, sensor=s, control=c)
    db.session.add(prop)
    db.session.commit()


def test_grow_system(mocked_device_with_sensor_and_control):
    dev, s, c = mocked_device_with_sensor_and_control

    prop = GrowProperty(name='ph', description='ph of the solution')
    prop_inst = GrowPropertyInstance(grow_property=prop, sensor=s, control=c)

    prop2 = GrowProperty(name='ec', description='ec of the solution')
    prop_inst2 = GrowPropertyInstance(grow_property=prop, sensor=s, control=c)
    db.session.add(prop_inst, prop_inst2)

    nft = GrowSystem(name='NFT', description='nutrient film technique')
    nft.properties = [prop, prop2]
    my_nft = GrowSystemInstance(grow_system=nft, device=dev)
    db.session.add(my_nft)
    db.session.commit()
