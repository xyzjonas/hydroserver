import logging

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from app.cache import Cache
from app.config import Config

SCAN_SLEEP = 2
CACHE = Cache()

db = SQLAlchemy()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
log = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # from app.models import db
    db.init_app(app)
    # global db
    db.app = app
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        # ... no changes to logging setup
        pass

    CORS(app, resources={r'/*': {'origins': '*'}})

    # with app.app_context():
    db.drop_all()
    db.create_all()

    return app


# [1] instantiate the app
# app = Flask(__name__)
# app.config.from_object(Config)


def init_device(dev):
    status = dev.read_status()
    if status.is_success:
        d = models.Device.from_status_response(dev, status.data)
        db.session.add(d)
        db.session.commit()
        CACHE.add_active_device(dev)
        return True
    return False


from app import models