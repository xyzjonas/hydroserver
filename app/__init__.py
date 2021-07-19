import logging

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.cache import CACHE
from app.config import Config

SCAN_SLEEP = 2

db = SQLAlchemy()
migrate = Migrate()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
log = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    # global db
    db.app = app

    # flask migrate
    migrate.init_app(app, db)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        # ... no changes to logging setup
        pass

    CORS(app, resources={r'/*': {'origins': '*'}})

    # todo: remove
    # db.drop_all()
    # db.create_all()
    # devices = models.Device.query.all()

    from app.scheduler.plugins import PLUGIN_MANAGER
    PLUGIN_MANAGER.initialize(Config.PLUGIN_PATHS)

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
