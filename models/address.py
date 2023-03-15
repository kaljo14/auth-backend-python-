from . import db

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.client_number'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    meter_readings = db.relationship('Meter', backref='meter_readings_relationship')

    def __init__(self, user_id, address):
        self.user_id = user_id
        self.address = address
