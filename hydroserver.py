import sys

from app import create_app
from app.core.cache import CACHE
from app.models import db, Device

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Device': Device, 'cache': CACHE}


def init():
    args = sys.argv
    if 'db' in args:
        return

    if 'run' in args:
        pass

    # Start-up: loading (health-check) devices from database, caching
    from app.system.device_controller import refresh_devices
    refresh_devices()

    # refresh/import configured systems/properties
    from app.grow.models import load_from_lists
    load_from_lists(
        properties=app.config.get("DEFAULT_GROW_PROPERTIES"),
        systems=app.config.get("DEFAULT_SYSTEMS")
    )


init()
