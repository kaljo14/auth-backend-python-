from datetime import datetime
from . import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'
    client_number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    egn_hash = db.Column(db.String(100), nullable=False)
    addresses = db.relationship('Address', backref='user_addresses_relationship')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, client_number, name, email, egn_hash, addresses=None):
        self.client_number = client_number
        self.name = name
        self.email = email
        self.egn_hash = bcrypt.generate_password_hash(egn_hash).decode('utf-8')
        self.addresses = addresses or []

    def check_egn_hash(self, egn_hash):
        return bcrypt.check_password_hash(self.egn_hash, egn_hash)
