from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from views.user import user_blueprint
from views.address import address_blueprint
from views.meter import meter_blueprint
from views.reading import reading_blueprint

app.register_blueprint(user_blueprint)
app.register_blueprint(address_blueprint)
app.register_blueprint(meter_blueprint)
app.register_blueprint(reading_blueprint)

from models.user import User
from models.address import Address
from models.meter import Meter
from models.reading import Reading

db.create_all()
