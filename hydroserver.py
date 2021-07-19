import sys

from app import create_app
from app.cache import CACHE
from app.models import db, Device

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Device': Device, 'cache': CACHE}


args = sys.argv
if 'run' in args:
    # initialize plug-in tasks
    from app.scheduler.plugins import PLUGIN_MANAGER
    PLUGIN_MANAGER.initialize(app.Config.PLUGIN_PATHS)

    # todo: move to flask-manger (run only)
    # Start-up: loading (health-check) devices from database, caching
    from app.main.device_controller import init_devices
    init_devices()
