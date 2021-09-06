import datetime
import logging
from functools import lru_cache

from croniter import croniter, CroniterNotAlphaError, CroniterBadCronError
from flask import jsonify, request

from app.system import bp
from app.system.device_controller import (
    Controller, ControllerError,
    run_scheduler, register_device, scan_devices, refresh_devices
)
from app.core.cache import CACHE
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
    devices = db.session.query(Device).all()
    response = [d.dictionary for d in devices]
    return jsonify(response)


@bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    d = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify(d.dictionary)


@bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    d = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    try:
        db.session.delete(d)
        db.session.commit()
    except Exception as e:
        return f"Delete failed '{e}'", 500
    return f"device '{device_id}' deleted.", 200


@bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    d = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([s.dictionary for s in d.sensors])


@lru_cache(maxsize=16)
def cached_call(current_hour, sensor_id, since_, count_):
    """Cache the least recently called histories. Assuming the client
    mostly doesn't need very precise data, it can sent rounded-up timestamps.
    In combination with the current hour datetime, the response can than
    be cached here, to further lower server load."""
    sensor = db.session.query(Sensor).filter_by(id=_get_id(sensor_id)).first_or_404()
    return sensor.get_last_values(since=since_, count=count_)


@bp.route('/devices/<int:device_id>/sensors/<int:sensor_id>/history', methods=['GET'])
def get_device_sensor_history(device_id, sensor_id):
    # expect timestamp in MILLISECONDS, don't make any assumptions
    timestamp_millis_string = request.args.get("since")
    since_datetime = None
    if timestamp_millis_string:
        try:
            since_datetime = datetime.datetime.fromtimestamp(
                int(timestamp_millis_string)/1000  # convert millis -> seconds
            )
        except (TypeError, ValueError) as e:
            return f"'{timestamp_millis_string}' Invalid value 'since' supplied: {e}", 400
    count = None
    if request.args.get("count"):
        try:
            count = int(request.args.get("count"))
        except (TypeError, ValueError) as e:
            return f"Invalid value 'count' supplied: {e}", 400

    # Cache the result with the current hour datetime as well.
    now = datetime.datetime.utcnow()
    now = datetime.datetime(now.year, now.month, now.day, now.hour, 0, 0)
    items = cached_call(now, sensor_id, since_datetime, count)
    return jsonify(items), 200


@bp.route('/devices/<int:device_id>/sensors/<int:sensor_id>', methods=['POST'])
def post_device_sensor(device_id, sensor_id):
    s = db.session.query(Sensor).filter_by(id=_get_id(sensor_id)).first_or_404()
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
    d = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    db.session.query()
    return jsonify([c.dictionary for c in d.controls])


@bp.route('/devices/<int:device_id>/controls/<int:control_id>', methods=['POST'])
def post_device_control(device_id, control_id):
    db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    c = db.session.query(Control).filter_by(id=_get_id(control_id)).first_or_404()
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
    d = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([t.dictionary for t in d.tasks])


@bp.route('/devices/<int:device_id>/tasks/<int:task_id>', methods=['DELETE'])
def delete_device_task(device_id, task_id):
    db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    task = db.session.query(Task).filter_by(id=_get_id(task_id)).first_or_404()
    if task.locked:
        return f"task '{task_id}' is locked.", 400
    db.session.delete(task)
    db.session.commit()
    return f"task '{task_id}' deleted", 200


@bp.route('/devices/<int:device_id>/tasks/<int:task_id>/pause', methods=['POST'])
def pause_device_task(device_id, task_id):
    db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    task = db.session.query(Task).filter_by(id=_get_id(task_id)).first_or_404()
    task.paused = True
    db.session.commit()
    return f'Task {task_id} paused.', 200


@bp.route('/devices/<int:device_id>/tasks/<int:task_id>/resume', methods=['POST'])
def resume_device_task(device_id, task_id):
    db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    task = db.session.query(Task).filter_by(id=_get_id(task_id)).first_or_404()
    task.paused = False
    db.session.commit()
    return f'Task {task_id} resumed.', 200


@bp.route('/devices/<int:device_id>/tasks', methods=['POST'])
def post_device_tasks(device_id):
    device = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json

    if not data:
        return "No data received", 400

    if not data.get("type"):
        return "'type' field required", 400

    # Are we creating a new item or modifying an existing one...?
    created = False
    if "id" in data:
        task = db.session.query(Task).filter_by(id=data["id"]).first()
        if not task:
            return f"No such task '{data['id']}'for device {device.name}", 400
    else:
        task = Task(device=device)
        created = True

    # SANITIZING input
    if data.get("control"):
        control = db.session.query(Control).filter_by(name=data["control"],
                                          device=device).first()
        if not control:
            return f"{device.name}: no such control '{data['control']}", 400
        task.control = control

    if data.get("sensor"):
        sensor = db.session.query(Sensor).filter_by(name=data["sensor"], device=device).first()
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
        run_scheduler(device.uuid)
    return (f"New task created: {task_info}", 201) if created \
        else (f"Task {task_info} modified: ", 200)


@bp.route('/devices/<int:device_id>', methods=['POST'])
def modify_device(device_id):
    device = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
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
    device_db = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "control" not in data:
        return "'control' field is required", 400

    control = db.session.query(Control) \
        .filter_by(name=data["control"], device=device_db) \
        .first_or_404(description=f"No such control {data['control']}")
    try:
        Controller(device_db).action(control, value=data.get('value', None))
        return f"{device_db.name}: '{control.name}' cmd success", 200
    except ControllerError as e:
        return f"{device_db.name}: '{control.name}' cmd failed: {e}", 500


@bp.route('/devices/<string:device_id>/categorize', methods=['POST'])
def post_device_categorize(device_id):
    device = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
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
    device = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    control = db.session.query(Control).filter_by(id=_get_id(control_id)).first_or_404()

    name = control.name
    device.put_unknown_command(name, control.state)
    db.session.delete(control)
    db.session.commit()
    return f"'{name}' deleted.", 200


@bp.route('/devices/<string:device_id>/sensors/<int:sensor_id>', methods=['DELETE'])
def delete_sensor(device_id, sensor_id):
    device = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    sensor = db.session.query(Sensor).filter_by(id=_get_id(sensor_id)).first_or_404()

    name = sensor.name
    device.put_unknown_command(name, sensor.last_value)
    db.session.delete(sensor)
    db.session.commit()
    return f"'{name}' deleted.", 200


@bp.route('/devices/<string:device_id>/scheduler', methods=['POST'])
def device_run_scheduler(device_id):
    device_db = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    try:
        run_scheduler(device_db.uuid)
    except ControllerError as e:
        return f"{e}", 500
    return f"'{device_db.name}' executor started.", 200


@bp.route('/devices/register', methods=['POST'])
def route_register_device():
    data = request.json
    if not data or 'url' not in data or data.get('url') is None:
        return "'url' field needed.", 400

    url = data['url']
    try:
        register_device(url)
    except ControllerError as e:
        return f"Device registration failed: {e}", 500
    return f"Device '{url}' registered", 201


@bp.route('/devices/scan', methods=['POST'])
def route_scan_devices():
    """Performs scan for new (yet unrecognized) devices."""
    found_devices = scan_devices()
    return f"Scan complete, {len(found_devices)} found devices {found_devices}.", 200


@bp.route('/devices/<string:device_id>/refresh', methods=['POST'])
def route_refresh_device(device_id):
    """Performs the 'init' operation - iterates through DB stored devices and tries
    to initialize them and store in cache (if not already there)."""
    device_db = db.session.query(Device).filter_by(id=_get_id(device_id)).first_or_404()
    try:
        refresh_devices(devices=[device_db])
    except ControllerError as e:
        return f'Failed to refresh: {e}', 500
    return "Refresh done", 200
