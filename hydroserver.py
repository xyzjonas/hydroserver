import sys

from app import create_app
from app.core.cache import CACHE
from app.models import db, Device

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Device': Device, 'cache': CACHE}


args = sys.argv
if 'run' in args:
    # initialize plug-in tasks
    from app.core.plugins import PLUGIN_MANAGER
    PLUGIN_MANAGER.initialize(app.config['PLUGIN_PATHS'])

    # Start-up: loading (health-check) devices from database, caching
    from app.system.device_controller import refresh_devices
    refresh_devices()
