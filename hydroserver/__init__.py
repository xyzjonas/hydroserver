import logging

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from hydroserver.cache import Cache
from hydroserver.config import Config

SCAN_SLEEP = 2
CACHE = Cache()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
log = logging.getLogger(__name__)


# [1] instantiate the app
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


def init_device(dev):
    status = dev.read_status()
    if status.is_success:
        d = models.Device.from_status_response(dev, status.data)
        db.session.add(d)
        db.session.commit()
        return True
    return False


# [2] enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

from hydroserver import routes, models
from hydroserver.scheduler import Scheduler
from hydroserver.device.serial import scan

# todo: REMOVE
# [3] clear DB
log.info("dropping database...")
db.drop_all()
log.info("recreating database...")
db.create_all()


found_devices = scan(exclude=[dev.port for dev in CACHE.get_all_active_devices()])
for device in found_devices:
    if init_device(device):
        CACHE.add_active_device(device)
