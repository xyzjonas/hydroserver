import threading

from croniter import croniter, CroniterNotAlphaError, CroniterBadCronError
from flask import jsonify, request

from hydroserver import app, CACHE, db, init_device
from hydroserver.models import Device, Task, Control, Sensor
from hydroserver.device import DeviceException
from hydroserver.device.serial import scan
from hydroserver.scheduler import Scheduler


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
    response = [d.dictionary for d in devices]
    return jsonify(response)


@app.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify(d.dictionary)


@app.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([s.dictionary for s in d.sensors])

# todo:post_device_sensors


@app.route('/devices/<int:device_id>/controls', methods=['GET'])
def get_device_controls(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([c.dictionary for c in d.controls])


@app.route('/devices/<int:device_id>/controls', methods=['POST'])
def post_device_controls(device_id):
    # todo: (!) active device keeps adding new controls/sensors if e.g. renamed
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400
    if "control" not in data:
        return "'control' field is required", 400
    c = Control.query.filter_by(name=data["control"], device=d).first()
    if not c:
        return f"No such control '{data['control']}", 400

    changes = {}
    for key, value in data.items():
        try:
            changes[getattr(c, key)] = value
            setattr(c, key, value)
        except AttributeError:
            pass

    db.session.commit()

    changes = [f"'{k}' -> '{v}'" for k, v in changes.items()]
    return f"'{c.name}' modified: {changes}"


@app.route('/devices/<int:device_id>/tasks', methods=['GET'])
def get_device_tasks(device_id):
    d = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    return jsonify([t.dictionary for t in d.tasks])


@app.route('/devices/<int:device_id>/tasks', methods=['DELETE'])
def delete_device_tasks(device_id):
    # todo: make a generic 'delete' function
    Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "id" not in data:
        return "task 'id' field is required", 400

    task_id = data["id"]
    task = Task.query.filter_by(id=_get_id(task_id)).first()
    if not task:
        return f"No such task '{task_id}'", 400
    db.session.delete(task)
    db.session.commit()
    return f"task '{task_id}' deleted", 200


@app.route('/devices/<int:device_id>/tasks', methods=['POST'])
def post_device_tasks(device_id):
    device = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "control" not in data:
        return "'control' field is required", 400

    control = Control.query.filter_by(name=data["control"], device=device).first()
    if not control:
        return f"{device.name}: no such control '{data['control']}", 400

    if data.get("sensor") and data["sensor"] not in [s.name for s in device.sensors]:
        return f"{device.name}: no such sensor '{data['sensor']}", 400

    # Are we creating a new item or modifying an existing one...?
    created = False
    if "id" in data:
        task = Task.query.filter_by(id=data["id"]).first()
        if not task:
            return f"No such task for device {device.name}", 400
        task.control = control
    else:
        task = Task(control=control, device=device)
        created = True

    # Fill the rest
    if data.get("name"):
        task.name = data.get("name")
    if data.get("cron"):
        try:
            croniter(data["cron"])
        except (CroniterNotAlphaError, CroniterBadCronError):
            return f"Invalid cron definition: '{data['cron']}'", 400
        task.cron = data.get("cron")
    if data.get("condition"):
        task.condition = data.get("condition")
    if data.get("sensor"):
        sensor = Sensor.query.filter_by(name=data["sensor"], device=device).first()
        task.sensor = sensor
    if data.get("type"):
        task.type = data.get("type")
    # todo: refactor
    if data.get("interval"):
        def __sanitize(string: str):
            i = string.split(",")
            if len(i) == 2:
                try:
                    left, right = [float(j) for j in i]
                    return f"[{left}, {right}]"
                except Exception:
                    pass
        if __sanitize(data.get("interval")):
            task.interval = __sanitize(data.get("interval"))

    db.session.add(task)
    db.session.commit()

    if created and len(Task.query.all()) == 1:
        # start up the scheduler for the device
        executor = Scheduler(CACHE.get_active_device(device.uuid))
        CACHE.add_scheduler(device.uuid, executor)
        threading.Thread(target=executor.run).start()

    return (f"New task created: {task}", 201) if created \
        else (f"Task modified: {task}", 200)


@app.route('/devices/<int:device_id>', methods=['POST'])
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


@app.route('/devices/<string:device_id>/action', methods=['POST'])
def device_action(device_id):
    device_db = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    data = request.json
    if not data:
        return "No data received", 400

    if "control" not in data:
        return "'control' field is required", 400

    control = Control.query.filter_by(name=data["control"], device=device_db).first()
    if not control:
        return f"{device_db.name}: no such control '{data['control']}'", 400

    # command = f"action_{control.name}"

    device = CACHE.get_active_device(device_db.uuid)
    if not device:
        return f"{device_db.name} not connected", 503

    try:
        response = device.send_control(control.name)
        if not response.is_success:
            return f"{device}: '{control.name}' ERROR - {response}", 500

        control.state = response.data
        db.session.commit()
        return f"{device}: '{control.name}' cmd sent successfully: {response}", 200
    except DeviceException as e:
        return f"{device}: '{control.name}' cmd failed: {e}", 500


@app.route('/devices/<string:device_id>/scheduler', methods=['POST'])
def device_run_scheduler(device_id):
    device_db = Device.query.filter_by(id=_get_id(device_id)).first_or_404()
    if CACHE.has_active_scheduler(device_db.uuid):
        return f"'{device_db.name}' has already an active executor.", 200
    # start up the scheduler for the device
    executor = Scheduler(CACHE.get_active_device(device_db.uuid))
    CACHE.add_scheduler(device_db.uuid, executor)
    threading.Thread(target=executor.run).start()
    return f"'{device_db.name}' executor started.", 200


@app.route('/cache', methods=['GET'])
def get_cache():
    data = {}
    for d in CACHE.get_all_active_devices():
        data[d.uuid] = {
            "device": str(d),
            "scheduler": str(CACHE.get_active_scheduler(d.uuid))
        }
    return jsonify(data), 200


@app.route('/devices/scan', methods=['POST'])
def scan_devices():
    CACHE.clear()
    found_devices = scan()
    for device in found_devices:
        if init_device(device):
            CACHE.add_active_device(device)
    return f"Scan complete, {len(found_devices)} found devices {found_devices}.", 200
