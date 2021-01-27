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

    # This is what remote device (Arduino) will understand
    PRECONFIGURED_MAPPINGS = {
        "sensors": {
            "temp": {
                "description": "air temperature",
                "unit": "°C"
            },
            "hum": {
                "description": "air humidity",
                "unit": "%"
            },
            "water_level": {
                "description": "water level",
                "unit": "NaN"
            }
        },
        "controls": {
            "switch_01": {
                "description": "switch 1"
            },
            "switch_02": {
            },
            "blink": {
                "description": "Just a blinking LED"
            },
        }

    }
