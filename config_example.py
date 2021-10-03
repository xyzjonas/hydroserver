import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'psql:///' + os.path.join(basedir, 'hydro.db')
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
DEFAULT_GROW_PROPERTIES = [
    {
        'name': 'EC',
        'color': '#ff6f00',
        'description': 'nothing of importance',
    },
    {
        'name': 'pH',
        'color': '#82caaf',
        'description': 'nothing of importance'
    },
    {
        'name': 'water flow',
        'description': 'nothing of importance',
        'color': '#194a8d'
    },
    {
        'name': 'reservoir',
        'color': '#75c0e0',
        'description': 'reservoir capacity'
    },
    {
        'name': 'water temperature',
        'description': 'nothing of importance'
    },
    {
        'name': 'air temperature',
        'description': 'nothing of importance'
    },
    {
        'name': 'air humidity',
        'description': 'nothing of importance'
    },
]
DEFAULT_SYSTEMS = [
    {
        'name': 'NFT',
        'required_properties': ['EC', 'pH', 'reservoir', 'water flow']
    },
    {
        'name': 'Grow tent',
        'required_properties': ['air temperature', 'air humidity']
    }
]
