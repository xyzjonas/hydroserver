import logging
from datetime import date

from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.core.cache import CACHE
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

    from app.system import bp as main_bp
    app.register_blueprint(main_bp)

    from app.grow import bp as grow_bp
    app.register_blueprint(grow_bp, url_prefix='/grow')

    global config
    config = app.config

    CORS(app, resources={r'/*': {'origins': '*'}})



    return app


from app import models
from app.grow import models
