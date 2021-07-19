from app import create_app
from app.cache import CACHE
from app.models import db, Device

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Device': Device, 'cache': CACHE}


# Start-up: loading (health-check) devices from database, caching
from app.main.device_controller import init_devices
init_devices()

# Initial scan (db population)
# for device in scan():
#     init_device(device)
