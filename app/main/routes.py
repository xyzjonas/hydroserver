import logging

from croniter import croniter, CroniterNotAlphaError, CroniterBadCronError
from flask import jsonify, request

from app.main import bp
from app.main import device_controller
from app.cache import CACHE
# from app.main.device_controller import ControllerError, run_scheduler, \
#     device_action, device_register, device_scan
from app.models import db, Device, Task, Control, Sensor

log = logging.getLogger(__name__)


def _get_id(string_or_int):
    if type(string_or_int) is int:
        return string_or_int
    elif type(string_or_int) is str:
        return int(string_or_int)
    else:
        raise ValueError("Supplied id value must be 'str' or 'int'")


@bp.route('/', methods=['GET'])
def root():
    # supported tasks
    # version
    # up-time
    # cache?
    data = {
        'version': '0.0.1',
        'up-time': 2123452,
        'active devices': [str(d) for d in CACHE.get_all_active_devices()]
    }
    return jsonify(data)


@bp.route('/devices', methods=['GET'])
def all_devices():
    devices = Device.query.all()
    response = [d.dictionary for d in devices]
    return jsonify(response)


@bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify(d.dictionary)


@bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    try:
        db.session.delete(d)
        db.session.commit()
    except Exception as e:
        return f"Delete failed '{e}'", 500
    return f"device '{device_id}' deleted.", 200


@bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([s.dictionary for s in d.sensors])


@bp.route('/devices/<int:device_id>/sensors/<int:sensor_id>', methods=['POST'])
def post_device_sensor(device_id, sensor_id):
    s = Sensor.query.filter_by(id=_get_id(sensor_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "description" in data:
        s.description = data["description"]
        db.session.commit()
        return f"'{s.name}' modified.", 200

    return f"'{s.name}' not modified.", 304


@bp.route('/devices/<int:device_id>/controls', methods=['GET'])
def get_device_controls(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([c.dictionary for c in d.controls])


@bp.route('/devices/<int:device_id>/controls/<int:control_id>', methods=['POST'])
def post_device_control(device_id, control_id):
    c = Control.query.filter_by(id=_get_id(control_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "description" in data:
        c.description = data["description"]
        db.session.commit()
        return f"'{c.name}' modified.", 200

    return f"'{c.name}' not modified.", 304


@bp.route('/devices/<int:device_id>/tasks', methods=['GET'])
def get_device_tasks(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([t.dictionary for t in d.tasks])


@bp.route('/devices/<int:device_id>/tasks/<int:task_id>', methods=['DELETE'])
def delete_device_task(device_id, task_id):
    task = Task.query.filter_by(id=_get_id(task_id)).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return f"task '{task_id}' deleted", 200


@bp.route('/devices/<int:device_id>/tasks', methods=['POST'])
def post_device_tasks(device_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json

    if not data:
        return "No data received", 400

    if not data.get("type"):
        return "'type' field required", 400

    # Are we creating a new item or modifying an existing one...?
    created = False
    if "id" in data:
        task = Task.query.filter_by(id=data["id"]).first()
        if not task:
            return f"No such task '{data['id']}'for device {device.name}", 400
    else:
        task = Task(device=device)
        created = True

    # SANITAZING input
    if data.get("control"):
        control = Control.query.filter_by(name=data["control"],
                                          device=device).first()
        if not control:
            return f"{device.name}: no such control '{data['control']}", 400
        task.control = control

    if data.get("sensor"):
        sensor = Sensor.query.filter_by(name=data["sensor"], device=device).first()
        if not sensor:
            return f"{device.name}: no such sensor '{data['sensor']}", 400
        task.sensor = sensor

    if data.get("cron"):
        try:
            croniter(data["cron"])
        except (CroniterNotAlphaError, CroniterBadCronError):
            return f"Invalid cron definition: '{data['cron']}'", 400
        task.cron = data.get("cron")

    # Fill the rest
    if data.get("name"):
        task.name = data.get("name")

    if data.get("condition"):
        task.condition = data.get("condition")

    if data.get("type"):
        task.type = data.get("type")

    if data.get("meta") and type(data.get("meta")) == dict:
        task.task_metadata = data.get("meta")

    db.session.add(task)
    db.session.commit()
    task_info = f"<id={task.id}name={task.name}>"

    if created:  # start up the scheduler for the device
        device_controller.run_scheduler(device)
    return (f"New task created: {task_info}", 201) if created \
        else (f"Task {task_info} modified: ", 200)


@bp.route('/devices/<int:device_id>', methods=['POST'])
def modify_device(device_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    modifiable = ["name"]  # makes sure it's a proper attribute
    was_modified = False
    for key, value in data.items():
        if key not in modifiable:
            continue
        device.__setattr__(key, value)
        was_modified = True
    db.session.add(device)
    db.session.commit()
    return (f"{device} modified.", 200) if was_modified \
        else (f"No changes", 200)


@bp.route('/devices/<string:device_id>/action', methods=['POST'])
def device_action(device_id):
    device_db = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "control" not in data:
        return "'control' field is required", 400

    control = Control.query.filter_by(
        name=data["control"], device=device_db) \
        .first_or_404(description=f"No such control {data['control']}")
    try:
        device_controller.device_action(device_db, control)
        return f"{device_db.name}: '{control.name}' cmd success", 200
    except device_controller.ControllerError as e:
        return f"{device_db.name}: '{control.name}' cmd failed: {e}", 500


@bp.route('/devices/<string:device_id>/categorize', methods=['POST'])
def post_device_categorize(device_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400
    name = data.get("name")
    if not name:
        return "'name' field required", 400
    t = data.get("type")
    if not t:
        return "'type' field required", 400
    unit = data.get("unit") or None
    description = data.get("description") or "unnamed"

    if t == "sensor":
        item = Sensor(name=data.get("name"), description=description,
                      unit=unit, device=device, last_value=-1)
    elif t == "control":
        item = Control(name=data.get("name"), description=description,
                       device=device, state=False)
    else:
        return f"Unrecognized sensor type '{t}'", 400

    db.session.add(item)
    cmds = device.unknown_commands
    del cmds[name]
    device.unknown_commands = cmds
    db.session.commit()
    return f"{t} successfully created", 201


@bp.route('/devices/<string:device_id>/controls/<int:control_id>', methods=['DELETE'])
def delete_control(device_id, control_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    control = Control.query.filter_by(id=_get_id(control_id)).first_or_404()

    name = control.name
    device.put_unknown_command(name, control.state)
    db.session.delete(control)
    db.session.commit()
    return f"'{name}' deleted.", 200


@bp.route('/devices/<string:device_id>/sensors/<int:sensor_id>', methods=['DELETE'])
def delete_sensor(device_id, sensor_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    sensor = Sensor.query.filter_by(id=_get_id(sensor_id)).first_or_404()

    name = sensor.name
    device.put_unknown_command(name, sensor.last_value)
    db.session.delete(sensor)
    db.session.commit()
    return f"'{name}' deleted.", 200


@bp.route('/devices/<string:device_id>/scheduler', methods=['POST'])
def device_run_scheduler(device_id):
    device_db = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    device_controller.run_scheduler(device_db)
    return f"'{device_db.name}' executor started.", 200


@bp.route('/devices/register', methods=['POST'])
def register_device():
    data = request.json
    if not data or 'url' not in data or data.get('url') is None:
        return "'url' field needed.", 400

    url = data['url']
    try:
        device_controller.device_register(url)
    except device_controller.ControllerError as e:
        return f"Device registration failed: {e}", 500
    return f"Device '{url}' registered", 201


@bp.route('/devices/scan', methods=['POST'])
def scan_devices():
    found_devices = device_controller.device_scan()
    return f"Scan complete, {len(found_devices)} found devices {found_devices}.", 200
