import logging

from flask import jsonify, request

from app import db
from app.grow import bp
from app.grow.models import GrowSystem, GrowProperty, GrowSystemInstance, GrowPropertyInstance
from app.models import Device
from app.utils import parse_id_as_int

log = logging.getLogger(__name__)


@bp.route('/systems', methods=['GET'])
def get_system_blueprints():
    systems = [s.dictionary for s in db.session.query(GrowSystem).all()]
    for syst in systems:
        syst['properties'].sort(key=lambda p: p['name'])
    return jsonify(systems), 200


@bp.route('/properties', methods=['GET'])
def get_system_properties():
    properties = [s.dictionary for s in db.session.query(GrowProperty).all()]
    return jsonify(properties), 200


# TODO: make this a param (filter)
@bp.route('/systems/<int:device_id>', methods=['GET'])
def get_system(device_id):
    d = db.session \
        .query(GrowSystemInstance) \
        .filter_by(device_id=parse_id_as_int(device_id)) \
        .first_or_404()
    d = d.dictionary
    # sort the properties
    d['properties'].sort(key=lambda p: p['name'])
    return jsonify(d), 200


@bp.route('/systems/new', methods=['POST'])
def add_system():
    data = request.json
    if not data:
        return f'data is empty', 400

    if not data.get('name'):
        return "Name field is required for a new grow system.", 400
    system = GrowSystem(name=data['name'])

    grow_properties_before = [prop.id for prop in system.properties]
    for prop in data.get('properties') or []:
        if prop['id'] in grow_properties_before:
            continue
        grow_property = db.session.query(GrowProperty).filter_by(id=prop['id']).first()
        if not grow_property:
            return f"Property id={prop['id']}, name={prop['name']} not found", 404
        system.properties.append(grow_property)

    db.session.add(system)
    db.session.commit()
    return 'Created.', 201


@bp.route('/systems/<int:system_id>', methods=['DELETE'])
def delete_system(system_id):
    system = db.session \
        .query(GrowSystem) \
        .filter_by(id=parse_id_as_int(system_id)) \
        .first_or_404()
    db.session.delete(system)
    db.session.commit()
    return "Deleted.", 200


@bp.route('/systems/<int:system_id>', methods=['POST'])
def edit_system(system_id):
    data = request.json
    if not data:
        return f'data is empty', 400

    system = db.session \
        .query(GrowSystem) \
        .filter_by(id=parse_id_as_int(system_id)) \
        .first_or_404()

    if data.get('name'):
        system.name = data['name']

    assigned_systems = db.session \
        .query(GrowSystemInstance) \
        .filter_by(grow_system_id=system.id) \
        .all()

    grow_properties_before = [prop.id for prop in system.properties]
    for prop_id in grow_properties_before:
        if not prop_id in [parse_id_as_int(prop.get('id')) for prop in data.get('properties')]:
            db.session \
                .query(GrowPropertyInstance) \
                .filter_by(property_id=prop_id) \
                .delete()
            system.properties.remove(
                db.session.query(GrowProperty).filter_by(id=prop_id).first())

    for prop in data.get('properties') or []:
        prop_id = parse_id_as_int(prop.get('id'))
        if prop_id in grow_properties_before:
            continue
        grow_property = db.session.query(GrowProperty).filter_by(id=prop_id).first()
        if not grow_property:
            return f"Property id={prop_id}, name={prop['name']} not found", 404

        system.properties.append(grow_property)
        for instance in assigned_systems:
            db.session.add(GrowPropertyInstance(grow_property=grow_property, grow_system=instance))

    db.session.commit()
    return 'Edited.', 200


@bp.route('/systems/assign', methods=['POST'])
def assign_system_to_device():
    """
    User chose to map a connected device to a type of system.
    Create a GrowSystemInstance based on the selected Grow instance.
    """
    data = request.json
    if not data:
        return f'data is empty', 400
    if not data.get('device_id'):
        return f'field \'device_id\' is required', 400
    if not data.get('system_id'):
        return f'field \'system_id\' is required', 400

    device_id = parse_id_as_int(data['device_id'])
    db.session.query(Device).filter_by(id=device_id).first_or_404()
    grow_system = db.session.query(GrowSystem).filter_by(id=data['system_id']).first_or_404()

    instance = db.session.query(GrowSystemInstance).filter_by(device_id=device_id).first()
    if not instance:
        instance = GrowSystemInstance.create_grow_system_instance(grow_system, device_id)
        db.session.add(instance)

    db.session.commit()
    return 'created', 201


@bp.route('/systems/unassign/<int:device_id>', methods=['DELETE'])
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


@bp.route('/properties/new', methods=['POST'])
def new_property():
    data = request.json
    if not data:
        return f'data is empty', 400
    if not data.get('name'):
        return f'Grow property name is required.', 400
    grow_property = GrowProperty(name=data['name'], description=data.get('description'))
    db.session.add(grow_property)
    db.session.commit()
    return "Created.", 201


@bp.route('/properties/<int:property_id>', methods=['POST'])
def edit_property(property_id):
    property_id = parse_id_as_int(property_id)

    grow_property = db.session.query(GrowProperty) \
        .filter_by(id=property_id) \
        .first_or_404()

    data = request.json
    if not data:
        return f'data is empty', 400

    if data.get('name'):
        grow_property.name = data.get('name')
    grow_property.description = data.get('description')

    db.session.commit()
    return "Changed.", 200


@bp.route('/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    property_id = parse_id_as_int(property_id)
    grow_property = db.session.query(GrowProperty) \
        .filter_by(id=property_id) \
        .first_or_404()

    db.session.delete(grow_property)
    db.session.commit()
    return "Deleted.", 200
