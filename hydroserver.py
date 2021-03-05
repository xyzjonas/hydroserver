from app import create_app, init_device
from app.cache import CACHE
from app.models import db, Device
from app.device import scan

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Device': Device, 'cache': CACHE}


# Initial scan (db population)
for device in scan():
    init_device(device)
