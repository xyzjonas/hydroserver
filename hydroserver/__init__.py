import logging
import threading
import time
import traceback

from datetime import datetime, timedelta
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# from server.hydroserver.serial import MyArduino
from hydroserver.config import Config


SCAN_SLEEP = 2
FOUND_DEVICES_MAP = {}


# logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
log = logging.getLogger(__name__)


# [1] instantiate the app
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# [2] enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


# todo: REMOVE
# [3] clear DB
log.info("dropping database...")
db.drop_all()
log.info("recreating database...")
db.create_all()


from hydroserver import routes, models
from hydroserver.serial import scan


def init_device(device):
    data = device.read_status()
    d = models.Device.query.filter_by(uuid=device.uuid).first()
    if d:
        d.is_online = True
        d.sensors = data
        db.session.commit()
    else:
        d = models.Device(uuid=device.uuid,
                          name=str(device),
                          is_online=True,
                          sensors=data)
        db.session.add(d)
    FOUND_DEVICES_MAP[device.uuid] = device


# [4] scan and load DB
# found_devices = scan()
# for dev in found_devices:
#     init_device(dev)
# db.session.commit()


def periodic_update():
    while True:
        time.sleep(SCAN_SLEEP)
        found_devices = scan(exclude=[dev.port for dev in FOUND_DEVICES_MAP.values()])
        for device in found_devices:
            init_device(device)

        if not FOUND_DEVICES_MAP:
            # log.error("No discovered device to scan.")
            continue
        try:
            to_be_deleted = []  # remove unresponsive devices at the end of the loop
            log.info(
                "Starting periodic update for: {}".format(FOUND_DEVICES_MAP))
            for uuid, device in FOUND_DEVICES_MAP.items():
                data = device.read_status()
                d = models.Device.query.filter_by(uuid=uuid).first()
                if not d:
                    log.error("No such device in database: {}".format(device))
                # todo: null
                d.sensors = data or {}
                d.is_online = device.is_responding
                db.session.commit()
                if device.is_responding:
                    d.last_seen_online = datetime.utcnow()
                else:
                    timeout = timedelta(seconds=20)
                    if datetime.utcnow() - d.last_seen_online > timeout:
                        log.warning("{}: not responding for {}, removing from scan..."
                                    .format(device.port, timeout))
                        to_be_deleted.append(uuid)
            for uuid in to_be_deleted:
                del FOUND_DEVICES_MAP[uuid]
        except Exception:
            traceback.print_exc()


threading.Thread(target=periodic_update).start()
