from datetime import datetime
from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity ,JWTManager
from flask_cors import CORS
from models import db, bcrypt, User,Address



app = Flask(__name__)
# CORS(app, origins=["http://localhost:8081"])
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/aut_python'
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



if __name__ == '__main__':
    app.run(debug=True)
