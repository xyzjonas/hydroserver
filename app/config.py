import datetime
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'hydro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = True
    SERIAL_PREFIX = "ttyUSB"
    BAUD_RATE = 19200
    INVERT_BOOLEAN = True  # Python <--> C - boolean inversion
    STATUS_OK = "ok"
    STATUS_FAIL = "error"

    # Scheduler
    RECONNECT_ATTEMPTS = 10
    IDLE_INTERVAL_SECONDS = 10
    SAFE_INTERVAL = 1.8  # seconds left to ignore and execute right away
    MAX_WORKERS = 4  # max threads to execute simultaneously

    PRECONFIGURED_COMMAND = {
        "ping": "ping",
        "status": "status",
        "control_prefix": "action_",
        "sensor_prefix": "read_"
    }

    PLUGIN_PATHS = ["/home/jobrauer/Documents/app_pluginsqapwo"]


class TestConfig(Config):
    TEST = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    IDLE_INTERVAL_SECONDS = 5
