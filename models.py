from datetime import datetime
from hydroserver import db
from hydroserver.serial import MyArduino


NOT_APPLICABLE = 'N/A'


class Device(db.Model):
    time_modified = db.Column(db.DateTime, nullable=True)
    last_seen_online = db.Column(db.DateTime, nullable=True)
    id = db.Column(db.Integer, primary_key=True)
    # Unique for device: hard-coded in the Arduino sketch
    uuid = db.Column(db.String(80), unique=True, nullable=False)
    # Human readable, user can change it to his liking
    name = db.Column(db.String(80), nullable=False)

    is_online = db.Column(db.Boolean(), nullable=False)
    sensors = db.Column(db.PickleType(), nullable=True)

    @property
    def dictionary(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'online': self.is_online,
            "time_modified": self.time_modified or NOT_APPLICABLE,
            "last_seen_online": self.last_seen_online or NOT_APPLICABLE,
            'sensors': self.sensors,
        }


from sqlalchemy import event
from sqlalchemy.orm.session import Session


@event.listens_for(Device, "before_insert")
@event.listens_for(Device, "before_update")
def my_before_insert_listener(mapper, connection, target):
    target.time_modified = datetime.utcnow()
