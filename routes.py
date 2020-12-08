from flask import jsonify, request

from hydroserver import app, FOUND_DEVICES_MAP, db
from hydroserver.models import Device


def _get_id(string_or_int):
    if type(string_or_int) is int:
        return string_or_int
    elif type(string_or_int) is str:
        return int(string_or_int)
    else:
        raise ValueError("Supplied id value must be 'str' or 'int'")


@app.route('/devices', methods=['GET'])
def all_devices():
    devices = Device.query.all()
    response = [d.to_dict() for d in devices]
    return jsonify(response)


@app.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify(d.dictionary)


@app.route('/devices/<int:device_id>', methods=['POST'])
def modify_device(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if data:
        app.logger.debug("POST received: {}".format(data))
        if "name" in data:
            d.name = data["name"]
            db.session.commit()
    return jsonify(d.dictionary)


@app.route('/devices/<string:device_id>/<string:action>', methods=['GET'])
def device_action(device_id, action):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    response = {'status': 'success'}
    serial_device = FOUND_DEVICES_MAP[device.uuid]
    try:
        serial_response = serial_device.send_command(action)
        response['data'] = serial_response
    except ConnectionError as e:
        response['status'] = 'failure'
        response['data'] = str(e)

    return jsonify(response)