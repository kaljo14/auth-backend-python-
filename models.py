from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    client_number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    egn_hash = db.Column(db.String(100), nullable=False)
    addresses = db.relationship('Address', backref='user_addresses_relationship')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   

    def __init__(self, client_number,name, email, egn_hash,addresses=[]):
        self.client_number =client_number
        self.name = name
        self.email = email
        self.egn_hash = bcrypt.generate_password_hash(egn_hash).decode('utf-8')
        self.addresses = addresses
    
    def check_egn_hash(self, egn_hash):
        return bcrypt.check_password_hash(self.egn_hash, egn_hash)


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.client_number'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    meter_readings = db.relationship('Meter', backref='meter_readings_relationship')
    
    def __init__(self,user_id,address):
        self.user_id= user_id
        self.address = address

class Meter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(20))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    installation_date = db.Column(db.Date)
    readings = db.relationship('Reading', backref='meter')

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meter.id'), nullable=False)
    reading_date = db.Column(db.Date)
    reading_value = db.Column(db.Float)

