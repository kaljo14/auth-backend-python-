from . import db

class Meter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(20))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    installation_date = db.Column(db.Date)
    readings = db.relationship('Reading', backref='meter')
