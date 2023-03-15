# users.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User

bp = Blueprint('users', __name__)

@bp.route('/api/register', methods=['POST'])
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

@bp.route('/api/user', methods=['GET'])
@jwt_required()
def user():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    return jsonify({'name': user
