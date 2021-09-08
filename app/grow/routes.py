import logging

from flask import jsonify, request

from app import db
from app.grow import bp
from app.grow.models import GrowSystem, GrowSystemInstance, GrowPropertyInstance, GrowProperty
from app.models import Device
from app.utils import parse_id_as_int

log = logging.getLogger(__name__)


@bp.route('/systems', methods=['GET'])
def get_system_blueprints():
    systems = [s.dictionary for s in db.session.query(GrowSystem).all()]
    for syst in systems:
        syst['properties'].sort(key=lambda p: p['name'])
    return jsonify(systems), 200


@bp.route('/systems/<int:device_id>', methods=['GET'])
def get_system(device_id):
    d = db.session \
        .query(GrowSystemInstance) \
        .filter_by(device_id=parse_id_as_int(device_id)) \
        .first_or_404()
    d = d.dictionary
    # sort the properties
    d['grow_properties'].sort(key=lambda p: p['name'])
    return jsonify(d), 200


@bp.route('/systems/<int:device_id>', methods=['POST'])
def assign_system_to_device(device_id):
    """
    User chose to map a connected device to a type of system.
    Create a GrowSystemInstance based on the selected Grow instance.
    """
    device_id = parse_id_as_int(device_id)
    device = db.session.query(Device).filter_by(id=device_id).first_or_404()
    data = request.json
    if not data:
        return f'data is empty', 400
    if not 'system_id':
        return f'field \'system_id\' is required', 400
    grow_system = db.session.query(GrowSystem).filter_by(id=data['system_id']).first_or_404()

    instance = db.session.query(GrowSystemInstance).filter_by(device_id=device_id).first()
    if not instance:
        instance = GrowSystemInstance.create_grow_system_instance(grow_system, device_id)
        db.session.add(instance)

    db.session.commit()
    return 'created', 201


@bp.route('/systems/<int:device_id>', methods=['DELETE'])
def unassign_system_from_device(device_id):
    instance = db.session.query(GrowSystemInstance).filter_by(device_id=device_id).first_or_404()
    db.session.delete(instance)
    db.session.commit()
    return 'Unassigned.', 200


@bp.route('/systems/<int:device_id>/properties/<int:property_id>', methods=['POST'])
def assign_control(device_id, property_id):
    """User chose to map an existing grow property instance to a device's sensor."""
    device_id = parse_id_as_int(device_id)
    property_instance_id = parse_id_as_int(property_id)

    data = request.json
    if not data:
        return f'data is empty', 400
    if not 'sensor_id':
        return f'field \'sensor_id\' is required', 400
    sensor_id = parse_id_as_int(data['sensor_id'])
    if not sensor_id:
        return f'\'sensor_id\' must be an integer', 400

    system_instance = db.session.query(GrowSystemInstance) \
        .filter_by(device_id=device_id) \
        .first_or_404()
    property_instance = db.session.query(GrowPropertyInstance) \
        .filter_by(id=property_instance_id) \
        .first_or_404()

    if sensor_id not in [sensor.id for sensor in system_instance.device.sensors]:
        return f'sensor \'{sensor_id}\' not attached to device \'{device_id}\'', 400

    property_instance.sensor_id = data['sensor_id']
    db.session.commit()
    return "Assigned.", 200



