import logging
import threading
import time
import traceback

from datetime import datetime
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# from server.hydroserver.serial import MyArduino
from hydroserver.config import Config
from hydroserver.serial import scan


SCAN_SLEEP = 2
FOUND_DEVICES_MAP = {}


# logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')


# [1] instantiate the app
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# [2] enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


from hydroserver import routes, models


# todo: REMOVE
# [3] clear DB
app.logger.info("dropping database...")
db.drop_all()
app.logger.info("recreating database...")
db.create_all()


# [4] scan and load DB
found_devices = scan()
for device in found_devices:
    data = device.read_status()
    d = models.Device(uuid=device.uuid,
                      name=str(device),
                      is_online=True,
                      sensors=data)
    db.session.add(d)
    FOUND_DEVICES_MAP[device.uuid] = device
db.session.commit()


def periodic_update():
    while True:
        time.sleep(SCAN_SLEEP)
        if not FOUND_DEVICES_MAP:
            app.logger.error("No discovered device to scan.")
            continue
        try:
            logging.info(
                "Starting periodic update for: {}".format(FOUND_DEVICES_MAP))
            for uuid, device in FOUND_DEVICES_MAP.items():
                data = device.read_status()
                d = models.Device.query.filter_by(uuid=uuid).first()
                if not d:
                    logging.error("No such device in database: {}".format(device))
                # todo: null
                d.sensors = data or {}
                d.is_online = device.is_responding
                db.session.commit()
                if device.is_responding:
                    d.last_seen_online = datetime.utcnow()
        except Exception:
            traceback.print_exc()



threading.Thread(target=periodic_update).start()
