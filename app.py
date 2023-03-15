from datetime import datetime
from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity ,JWTManager
from flask_cors import CORS
from models import db, bcrypt, User,Address,Meter,Reading



app = Flask(__name__)
# CORS(app, origins=["http://localhost:8081"])
cors = CORS(app, resources={r"/*": {"origins": "*"}})
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/aut_python'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test@192.168.99.245:5432/tester'
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    egn_hash = data.get('egn_hash')
    addresses = data.get('addresses')
    client_number = data.get('client_number')
    
    if not client_number or not name or not email or not egn_hash:
        return jsonify({'message': 'Missing required information'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    if User.query.filter_by(egn_hash=egn_hash).first():
        return jsonify({'message': 'User with EGN already exists'}), 400

    # Create new user and address objects
    user = User(client_number=client_number, name=name, email=email, egn_hash=egn_hash)
    for address in addresses:
        addr = Address(user_id=client_number, address= address["address"])
        db.session.add(addr)
     
    
    # Add user and address to database
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
# returns access token as header 
def login():
    data = request.json
    user = User.query.filter_by(client_number=data['client_number']).first()
    if not user or not user.check_egn_hash(data['egn_hash']):
        return jsonify({'message': 'Invalid credentials'}), 401
    access_token = create_access_token(identity=user.client_number)
    return jsonify({'access_token': access_token}), 200
# returns access token as cookie
# def login():
#     data = request.json
#     user = User.query.filter_by(email=data['email']).first()
#     if not user or not user.check_password(data['password']):
#         return jsonify({'message': 'Invalid credentials'}), 401
#     access_token = create_access_token(identity=user.id)
#     resp = make_response(jsonify({'message': 'Successfully logged in'}), 200)
#     resp.set_cookie('access_token', access_token, httponly=True)
#     return resp



@app.route('/api/user', methods=['GET'])
@jwt_required()
def user():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    return jsonify({'name': user.name, 'email': user.email}), 200

@app.route('/api/user/addresses', methods=['GET'])
@jwt_required()
def user_info_addresses():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    addresses = [address.address for address in user.addresses]
    return jsonify({'name': user.name, 'email': user.email ,'addresses':addresses}), 200



# test for the get all info route
@app.route('/api/users/total', methods=['GET'])
@jwt_required()
def get_all_users_info():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    user_dict = {
        'name': user.name,
        'email': user.email,
        'egn_hash':user.egn_hash,
        'created_at':user.created_at,
        'updated_at':user.updated_at,
        'client_number': user.client_number,
        'addresses': []
    }
    for address in user.addresses:
        address_dict = {
            'id': address.id,
            'user_id': address.user_id,
            'address': address.address,
            'meter_readings': []
        }
        for meter in address.meter_readings:
            meter_dict = {
                'id': meter.id,
                'meter_number': meter.meter_number,
                'address_id': meter.address_id,
                'installation_date': meter.installation_date,
                'readings': []
            }
            for reading in meter.readings:
                reading_dict = {
                    'id': reading.id,
                    'meter_id': reading.meter_id,
                    'reading_date': reading.reading_date,
                    'reading_value': reading.reading_value
                }
                meter_dict['readings'].append(reading_dict)
            address_dict['meter_readings'].append(meter_dict)
        user_dict['addresses'].append(address_dict)
    return jsonify(user_dict)

@app.route('/api/user/addReadings', methods=['POST'])
def add_readings():
    data =request.get_json()
    readings =data['readings']
    for reading in readings:
        new_reading = Reading(meter_id=reading['meter_id'],
                              reading_date=datetime.now().date(),
                           reading_value=reading['reading_value'])
        db.session.add(new_reading)
    db.session.commit()
    return jsonify({'message': 'New reading added successfully.'}), 201

if __name__ == '__main__':
    app.run(debug=True)
