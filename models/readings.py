from . import db

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meter.id'), nullable=False)
    reading_date = db.Column(db.Date)
    reading_value = db.Column(db.Float)
