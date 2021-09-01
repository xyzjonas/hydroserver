import logging
from datetime import date

from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.cache import CACHE
from app.config import Config

SCAN_SLEEP = 2

db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
config = None

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
log = logging.getLogger(__name__)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    db.app = app  # global db
    app.json_encoder = CustomJSONEncoder  # encode datetime as ISO

    # flask migrate
    opts = {"autoflush": False}
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True, session_options=opts)
    else:
        migrate.init_app(app, db, session_options=opts)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    global config
    config = app.config

    CORS(app, resources={r'/*': {'origins': '*'}})



    return app


# [1] instantiate the app
# app = Flask(__name__)
# app.config.from_object(Config)


# def init_device(dev):
#     status = dev.read_status()
#     if status.is_success:
#         d = models.Device.from_status_response(dev, status.data)
#         db.session.add(d)
#         db.session.commit()
#         CACHE.add_active_device(dev)
#         return True
#     return False


from app import models
