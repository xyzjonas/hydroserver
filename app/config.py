import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'hydro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = True

    # Serial connection defaults
    SERIAL_PREFIX = "ttyUSB"  # used during serial scan
    BAUD_RATE = 19200

    # Device status
    STATUS_INTERVAL_SECONDS = 10  # i.e. how often is status issued
    SENSOR_HISTORY_LOGGING_CRON = "*/20 * * * *"  # i.e. how often is sensor's value saved

    # Scheduler
    RECONNECT_ATTEMPTS = 10
    IDLE_INTERVAL_SECONDS = STATUS_INTERVAL_SECONDS  # deprecated
    SAFE_INTERVAL = 1.8  # seconds left to ignore and execute right away
    MAX_WORKERS = 4  # max threads to execute simultaneously

    # 'Protocol' settings
    STATUS_OK = "ok"
    STATUS_FAIL = "error"
    PRECONFIGURED_COMMAND = {
        "ping": "ping",
        "status": "status",
        "control_prefix": "action_",
        "sensor_prefix": "read_"
    }

    PLUGIN_PATHS = ["/home/jobrauer/Documents/app_pluginsqapwo"]

    # High level user definition of devices/attributes
    DEFAULT_ATTRIBUTES = {
        'ec': {
            'description': 'nothing of importance'
        },
        'ph': {
            'description': 'nothing of importance'
        },
        'reservoir': {
            'description': 'nothing of importance'
        },
        'light': {
            'description': 'nothing of importance'
        },
        'water_flow': {
            'description': 'nothing of importance'
        },
        'water_temperature': {
            'description': 'nothing of importance'
        },
        'air_temperature': {
            'description': 'nothing of importance'
        },
        'air_humidity': {
            'description': 'nothing of importance'
        },
    }
    DEFAULT_SYSTEMS = {
        'NFT': {
            'required_attributes': ['ec', 'ph', 'reservoir']
        }
    }


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    IDLE_INTERVAL_SECONDS = 5
